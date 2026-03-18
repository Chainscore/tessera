import asyncio

from typing import cast
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.storage.da.packages import PackageDA
from jam.storage.da.mappings import PackageStatus, PackageStatusMap
from tsrkit_types import Option, Uint, structure, U8, U64, String

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.connection import PeerConnection
from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature
from jam.types.work.package import WorkPackageBundle
from jam.types.work import SegmentRootLookup

from jam.utils.gather import gather_with_exceptions
from jam.utils.constants import X
from jam.telemetry import emit_event
from jam.telemetry.events import (
    SharingWorkPackage, WorkPackageSharingFailed, BundleSent,
    WorkPackageBeingShared, WorkPackageReceived, WorkPackageFailed,
    WorkPackageOutline
)
from tsrkit_types import Bytes32


@structure
class CoreSegment:
    core_index: CoreIndex
    segment_root_map: SegmentRootLookup


@structure
class Credential:
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature

    def __repr__(self):
        return f"Credential(wr_hash={self.work_report_hash.hex()}, sign={self.ed25519_signature.hex()[:16]}...)"


@structure
class CE134Response:
    len: Uint[32]
    cred: Credential

    @property
    def is_valid(self):
        if len(self.cred.encode()) == self.len:
            return True
        return False


@structure
class CE134Data:
    map_len: Uint[32]
    core_segment: CoreSegment
    bundle_len: Uint[32]
    work_package_bundle: WorkPackageBundle

    @property
    def is_valid(self):
        if (
            len(self.core_segment.encode()) == self.map_len
            and len(self.work_package_bundle.encode()) == self.bundle_len
        ):
            return True
        return False


OptCred = Option[Credential]


class WorkPackageSharing(NetworkProtocol):
    """
    CE 134 Protocol for sharing Work Package Bundle among Guarantors

    Protocol Flow:
        Guarantor -> Guarantor

        --> Core Index ++ Segments-Root Mappings
        --> Work-Package Bundle
        --> FIN
        <-- Work-Report Hash ++ Ed25519 Signature
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-134-work-package-sharing
    """

    _prefix = PrefixType.CE134

    async def transmit(self, data: CE134Data):
        """Request Work Report from Node"""
        node = self.jam.router.node
        state = self.jam.state

        msg_a = data.core_segment.encode()
        len_a = data.map_len.encode()
        msg_b = data.work_package_bundle.encode()
        len_b = data.bundle_len.encode()

        ci = data.core_segment.core_index

        # Fetch guarantors mapping
        from jam.utils.assignment import assign_guarantors

        mapping = assign_guarantors(self.jam)
        guarantors = mapping[0][ci]
        self.logger.debug(
            "Fetched Assigned Guarantors",
            mapping=mapping[1], tau=state.tau, root=state.root.hex()
        )

        self.logger.info(
            "Transmitting work package bundle to guarantors",
            core=ci,
            guarantors=guarantors,
            stream_a_size=data.map_len,
            stream_b_size=data.bundle_len,
            segment_map_length=len(data.core_segment.segment_root_map),
        )

        tasks = []
        transmitted_count = 0
        event_id = id(data) & 0xFFFFFFFFFFFFFFFF

        for client in node.all_connected:
            try:
                if client.val not in guarantors:
                    continue

                # Get peer_id for telemetry
                peer_id_bytes = getattr(client, 'peer_ed_key', bytes(32))
                if not isinstance(peer_id_bytes, bytes) or len(peer_id_bytes) != 32:
                    peer_id_bytes = bytes(32)
                
                # Emit SharingWorkPackage event
                emit_event(SharingWorkPackage(event_id=U64(event_id), peer_id=Bytes32(peer_id_bytes)))

                self.logger.trace("Transmitting bundle", peer=client.peer_id)

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

                transmitted_count += 1

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                res = client.close_and_wait(message=msg_b, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)
                
                # Emit BundleSent event
                emit_event(BundleSent(event_id=U64(event_id), peer_id=Bytes32(peer_id_bytes)))

                self.logger.debug(
                    "Work package bundle transmitted to guarantor",
                    stream_id=stream_id,
                    peer=client,
                    core=ci,
                )

            except Exception as e:
                # Emit WorkPackageSharingFailed event
                emit_event(WorkPackageSharingFailed(
                    event_id=U64(event_id), peer_id=Bytes32(peer_id_bytes), reason=String(str(e)[:100]))
                )

                self.logger.error(
                    "Failed to transmit work package bundle to guarantor",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        if transmitted_count > 2:
            print(
                "Trying to transmit work package bundle to more than 2 guarantors"
            )

        responses = await gather_with_exceptions(tasks)

        self.logger.info(
            "Work package bundle transmission completed",
            transmitted_to=transmitted_count,
            guarantors=guarantors,
            core=ci,
        )

        return responses

    async def req_intercept(self, stream_id: int, server: PeerConnection):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors"""
        settings = self.jam.settings

        buffer = server.stream_buffer[stream_id][1:]

        try:
            self.logger.debug(
                "Received work package bundle",
                stream_id=stream_id,
                peer=server,
                buffer_size=len(buffer),
            )

            data = CE134Data.decode(buffer)
            data = cast(CE134Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            bundle = data.work_package_bundle

            self.logger.trace("Validating Work Package..")
            from jam.incore.validator import Validator
            from jam.incore.error import ValidatorError

            validator = Validator()
            is_valid = validator.validate_wp(bundle.package)

            wp_da = PackageDA(settings.d3l)
            wp_status_da = PackageStatusMap(settings.d3l)
            wp_hash = bundle.package.hash()

            status = PackageStatus.empty()
            if not is_valid:
                status.status = String("FAILED")
                status.err = String("Invalid Work Package")
                wp_status_da.put(wp_hash, status)

                # TODO: Publish failed EVENT
                # TODO: Store WP as failed
                raise ValueError("Work Package isn't valid")

            self.logger.trace("Storing WP..", wp_hash=bundle.package.hash().hex()[:16]+"...")
            wp_da.put(bundle.package)

            status.status = String("REPORTABLE")
            wp_status_da.put(wp_hash, status)

            db = settings.main_db
            self.logger.debug("Storing Extrinsics..")
            extrinsics = bundle.extrinsics
            ext_da = ItemExtrinsics(db)
            ext_da.store_processed(extrinsics)

            # Generating report from work package bundle
            self.logger.trace("Building Work Report..")
            from jam.incore.processor import Processor

            processor = Processor(self.jam)
            wr, wr_hash = processor.process_bundle(
                core=data.core_segment.core_index,
                bundle=bundle,
                sr_lookup=data.core_segment.segment_root_map,
            )

            ed25519_key = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)

            # Build Guarantee
            self.logger.trace("Building guarantee..")
            payload = X.GUARANTEE.value + wr_hash.encode()

            # Sign the Guarantee
            self.logger.trace("Signing guarantee..")
            sign = Ed25519Signature(ed25519_key.sign(payload))

            # Build Credential
            cred = Credential(work_report_hash=wr_hash, ed25519_signature=sign)

            # Return Credential to OG Guarantor

            self.logger.trace(
                "Sharing guarantee..",
                wr_hash=wr_hash.hex()[:16] + "...",
                sign=sign.hex()[:16] + "...",
                to=server,
            )
            msg_a = cred.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send Messages with their lengths
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            self.logger.info(
                "Refined work package bundle and shared guarantee with guarantor.",
                stream_id=stream_id,
                guarantor=server,
                wp_hash=wp_hash.hex()[:16] + "...",
                wr_hash=wr_hash.hex()[:16] + "...",
                credential_size=len(cred.encode()),
            )

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            self.logger.error(
                "Error processing work package bundle",
                guarantor=server,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    async def res_intercept(self, stream_id: int, client: PeerConnection
                      ) -> tuple[Credential | None, PeerConnection]:
        """Intercept Report Guarantee from guarantors"""
        buffer = client.stream_buffer[stream_id]

        try:
            self.logger.trace(
                "Received report credential from guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data = CE134Response.decode(buffer)
            data = cast(CE134Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            self.logger.debug(
                "Received report guarantee.",
                stream_id=stream_id,
                peer=client,
                wr_hash=data.cred.work_report_hash.hex()[:16] + "...",
                sign=data.cred.ed25519_signature.hex()[:16] + "...",
            )

            return data.cred, client

        except Exception as e:
            self.logger.error(
                Code.BAD_RESPONSE,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

            return None, client
