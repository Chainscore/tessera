from typing import cast, TYPE_CHECKING

from tsrkit_types import Uint, U8, U16, structure

from jam.logging import get_logger
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.jamnp import JAMNP
from jam.network.peer import QuicPeer
from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data

from jam.types.protocol.crypto import Ed25519Signature, WorkReportHash
from jam.types.protocol.core import ValidatorIndex
from jam.types.work.report import WorkReport
from jam.storage.da import ReportsDA

# Module-specific logger
logger = get_logger("network")


@structure
class Judgment:
    """
    A judgment about a work-report as per CE 145 specification.
    Format: Epoch Index ++ Validator Index ++ Validity ++ Work-Report Hash ++ Ed25519 Signature
    """

    epoch_index: int  # EpochIndex as int type
    validator_index: ValidatorIndex
    validity: U8  # 0 = Invalid, 1 = Valid
    work_report_hash: WorkReportHash
    signature: Ed25519Signature

    @property
    def is_valid(self) -> bool:
        """Check if the judgment declares the work-report as valid"""
        return self.validity == U8(1)

    @property
    def is_invalid(self) -> bool:
        """Check if the judgment declares the work-report as invalid"""
        return self.validity == U8(0)


@structure
class CE145Data:
    """CE 145 protocol data structure"""

    len: Uint[32]
    judgment: Judgment

    @property
    def is_valid(self):
        if len(self.judgment.encode()) == self.len:
            return True
        return False


class WorkReportStorage:
    """Dummy work report storage for local WR management"""

    def __init__(self):
        self._storage = {}  # WR_hash -> WorkReport mapping

    def has_work_report(self, wr_hash: WorkReportHash) -> bool:
        """Check if work report exists in local storage"""
        return wr_hash.hex() in self._storage

    def get_work_report(self, wr_hash: WorkReportHash) -> WorkReport:
        """Get work report from local storage"""
        return self._storage.get(wr_hash.hex())

    def store_work_report(self, wr_hash: WorkReportHash, work_report: WorkReport):
        """Store work report in local storage"""
        self._storage[wr_hash.hex()] = work_report
        logger.debug("Work report stored locally", wr_hash=wr_hash.hex()[:16] + "...")


# Global work report storage instance
_wr_storage = WorkReportStorage()


def get_work_report_storage() -> WorkReportStorage:
    """Get the global work report storage instance"""
    return _wr_storage


class JudgmentPublication(NetworkProtocol):
    """
    CE 145 Protocol for publishing judgments about work-reports

    Protocol Flow:
    Auditor → prepare judgment [epoch_idx, validator_idx, validity, WR_hash, signature]
    → open CE_145_stream → send [prefix + len + judgment_payload] → FIN → close_stream

    Validator ← accept CE_145_stream ← receive [prefix + len + judgment_payload]
    ← verify_signature ← check WR_hash in storage → fetch via CE_136 if needed
    ← process judgment based on validity ← FIN ← close CE_145_stream

    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-145-judgment-publication
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE145

    async def transmit(self, data: CE145Data):
        """
        Transmit judgment from Auditor (client) to Validator (server)

        Auditor flow:
        → prepare judgment [epoch_idx, validator_idx, validity, WR_hash, signature]
        → open CE_145_stream
        → send [prefix + len + judgment_payload]
        → FIN
        → close_stream
        """
        from jam.network.node import node 

        msg_data = data.judgment.encode()
        len_data = data.len.encode()

        logger.info(
            "Publishing judgment to validators",
            epoch_index=data.judgment.epoch_index,
            validator_index=int(data.judgment.validator_index),
            validity="valid" if data.judgment.is_valid else "invalid",
            work_report_hash=data.judgment.work_report_hash.hex()[:16] + "...",
            validator_count=len(node._protocols),
        )

        published_count = 0
        responses = []

        # Broadcast to all connected validator peers
        for client in node._protocols.values():
            try:
                logger.debug(
                    "Publishing judgment to validator",
                    peer=str(client),
                    epoch_index=data.judgment.epoch_index,
                )

                # Open CE_145_stream and send [prefix + len + judgment_payload]
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send length and judgment data
                client.stream_and_keep_open(message=len_data, stream_id=stream_id)
                response = await client.close_and_wait(message=msg_data, stream_id=stream_id)

                responses.append(response)
                published_count += 1

                logger.debug(
                    "Judgment published to validator",
                    stream_id=stream_id,
                    epoch_index=data.judgment.epoch_index,
                )

            except Exception as e:
                logger.error(
                    "Failed to publish judgment to validator",
                    error=str(e),
                )

        logger.info(
            "Judgment publication completed",
            published_to=published_count,
            epoch_index=data.judgment.epoch_index,
            validity="valid" if data.judgment.is_valid else "invalid",
        )

        return responses

    def req_intercept(self, stream_id: int, server: JAMNP):
        """
        Intercept & Process judgment on Validator (server)

        Validator flow:
        ← accept CE_145_stream
        ← receive [prefix + len + judgment_payload]
        ← check if WR_hash exists in local storage
            if not: → fetch via CE_136
        ← process judgment based on validity
        ← FIN
        ← close CE_145_stream
        """
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received judgment publication on validator",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            # Receive [prefix + len + judgment_payload]
            data, _ = CE145Data.decode_from(buffer[1:])
            data = cast(CE145Data, data)

            if not data.is_valid:
                logger.warning("Invalid CE145 data received", stream_id=stream_id)
                return

            judgment = data.judgment

            logger.info(
                "Processing judgment on validator",
                stream_id=stream_id,
                epoch_index=judgment.epoch_index,
                validator_index=int(judgment.validator_index),
                validity="valid" if judgment.is_valid else "invalid",
                work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
            )

            # Step 1: Check if WR_hash exists in local storage
            wr_storage = get_work_report_storage()
            work_report = None

            if wr_storage.has_work_report(judgment.work_report_hash):
                logger.info(
                    "Work report found in local storage",
                    work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
                )
                work_report = wr_storage.get_work_report(judgment.work_report_hash)
            else:
                logger.info(
                    "Work report not in local storage, fetching via CE_136",
                    work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
                )
                # Fetch WR via CE_136 asynchronously
                import asyncio

                asyncio.create_task(
                    self._fetch_and_store_work_report(
                        server.node, judgment.work_report_hash, wr_storage
                    )
                )
                # For now, proceed without work report
                work_report = None

            # Step 3: Process judgment based on validity
            if judgment.validity == U8(0):  # Invalid work-report
                logger.info(
                    "Processing invalid judgment (validity = 0)",
                    stream_id=stream_id,
                    work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
                )

                # Store for disputes extrinsic
                self._store_judgment_for_disputes(judgment)

                # Broadcast to successors + neighbors + audit WR if not already
                import asyncio

                asyncio.create_task(
                    self._handle_invalid_judgment(server.node, judgment, work_report)
                )

            elif judgment.validity == U8(1):  # Valid work-report
                logger.info(
                    "Processing valid judgment (validity = 1)",
                    stream_id=stream_id,
                    work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
                )

                # Store judgment, may defer broadcast
                self._store_judgment_for_disputes(judgment)
                logger.debug("Valid judgment stored, broadcast deferred")

            else:
                logger.warning(
                    "Unknown validity value",
                    stream_id=stream_id,
                    validity=int(judgment.validity),
                )

            logger.info(
                "Judgment processed successfully on validator",
                stream_id=stream_id,
                epoch_index=judgment.epoch_index,
                validity=int(judgment.validity),
            )

            # Send FIN and close CE_145_stream
            server.stream_and_close(b"", stream_id)

        except Exception as e:
            logger.error(
                "Error processing judgment on validator",
                stream_id=stream_id,
                error=str(e),
            )
            # Send FIN and close stream even on error
            server.stream_and_close(b"", stream_id)

    # def _verify_judgment_signature(self, judgment: Judgment) -> bool:
    #     """
    #     Verify the Ed25519 signature of the judgment.
    #     TODO: Implement actual signature verification against validator keys
    #     """
    #     logger.debug(
    #         "Verifying judgment signature",
    #         validator_index=int(judgment.validator_index),
    #         signature_preview=judgment.signature.hex()[:16] + "..."
    #     )

    #     # TODO: Implement actual signature verification
    #     # For now, always return True
    #     return True

    async def _fetch_and_store_work_report(self, node: QuicPeer, wr_hash: WorkReportHash, wr_storage):
        """Fetch work report via CE_136 and store it"""
        work_report = await self._fetch_work_report_via_ce136(node, wr_hash)
        if work_report:
            wr_storage.store_work_report(wr_hash, work_report)
        return work_report

    async def _fetch_work_report_via_ce136(self, node: QuicPeer, wr_hash: WorkReportHash):
        """
        Fetch work report via CE_136 protocol

        → open CE_136_stream to fetch WR
        → request WR_hash via CE_136
        → receive WR data
        → close CE_136_stream
        """
        logger.info(
            "Fetching work report via CE_136",
            work_report_hash=wr_hash.hex()[:16] + "...",
        )

        try:
            # Create CE 136 request data
            work_report_request_data = CE136Data(
                len=Uint[32](len(wr_hash.encode())), work_report_hash=wr_hash
            )

            # Use CE 136 protocol to request work-report
            ce136_protocol = WorkReportRequest()
            responses = await ce136_protocol.transmit(node, work_report_request_data)

            if responses and len(responses) > 0:
                logger.info(
                    "Work report fetched successfully via CE_136",
                    work_report_hash=wr_hash.hex()[:16] + "...",
                    response_count=len(responses),
                )
                return responses[0]
            else:
                logger.warning(
                    "Failed to fetch work report via CE_136",
                    work_report_hash=wr_hash.hex()[:16] + "...",
                )
                return None

        except Exception as e:
            logger.error(
                "Error fetching work report via CE_136",
                work_report_hash=wr_hash.hex()[:16] + "...",
                error=str(e),
            )
            return None

    async def _handle_invalid_judgment(self, node: QuicPeer, judgment: Judgment, work_report):
        """
        Handle invalid judgment: broadcast to successors + neighbors + audit WR if not already
        """
        logger.info(
            "Handling invalid judgment",
            epoch_index=judgment.epoch_index,
            work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
        )

        # Broadcast to successors and neighbors
        await self._broadcast_to_successors_and_neighbors(node, judgment)

        # Audit WR if not already done and create own judgment
        if work_report and self._should_audit_work_report(node, judgment):
            logger.info(
                "Auditing work report and creating own judgment",
                epoch_index=judgment.epoch_index,
            )

            # Audit work report (always returns valid for now)
            our_validity = self._audit_work_report(work_report, judgment.work_report_hash)

            # Create our own judgment
            our_judgment = await self._create_own_judgment(
                node, judgment.epoch_index, judgment.work_report_hash, our_validity
            )

            if our_judgment:
                # Publish our own judgment
                our_ce145_data = CE145Data(
                    len=Uint[32](len(our_judgment.encode())), judgment=our_judgment
                )
                await self.transmit(node, our_ce145_data)

    async def _broadcast_to_successors_and_neighbors(self, node: QuicPeer, judgment: Judgment):
        """Broadcast invalid judgment to successors and neighbors"""
        logger.info(
            "Broadcasting invalid judgment to successors and neighbors",
            epoch_index=judgment.epoch_index,
        )

        broadcast_count = 0
        for client in node._protocols:
            try:
                # Send judgment to successor/neighbor
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_buffer[stream_id] = self._prefix.encode()

                msg_data = judgment.encode()
                len_data = Uint[32](len(msg_data)).encode()

                client.stream_and_keep_open(message=len_data, stream_id=stream_id)
                await client.close_and_wait(message=msg_data, stream_id=stream_id)

                broadcast_count += 1

                logger.debug(
                    "Invalid judgment broadcasted",
                    node_name=node.name,
                    peer_endpoint=f"{peer.host}:{peer.port}",
                    stream_id=stream_id,
                )

            except Exception as e:
                logger.error(
                    "Failed to broadcast invalid judgment",
                    error=str(e),
                )

        logger.info(
            "Invalid judgment broadcast completed",
            broadcast_to=broadcast_count,
        )

    async def auditor_create_judgment(
        self,
        node: QuicPeer,
        epoch_index: int,
        validator_index: int,
        work_report_hash: WorkReportHash,
    ) -> Judgment:
        """
        Main auditor function to create judgment with automatic WR fetching if needed.

        This is the primary function auditors must use to give their judgment.

        Args:
            node: The auditor node
            epoch_index: Current epoch index (int)
            validator_index: Auditor's validator index
            work_report_hash: Hash of work report to judge

        Returns:
            Judgment: The auditor's judgment on the work report

        Flow:
        1. Check if auditor has the required work report
        2. If not, fetch via CE136
        3. Audit the work report to determine validity
        4. Create and return judgment
        """
        from jam.settings import settings

        logger.info(
            "Auditor creating judgment",
            epoch_index=epoch_index,
            validator_index=validator_index,
            work_report_hash=work_report_hash.hex()[:16] + "...",
        )

        # Step 1: Check if auditor has the required work report
        d3l = settings.d3l
        wr_storage = ReportsDA(d3l)
        work_report = None

        if wr_storage.get(work_report_hash):
            logger.info(
                "Auditor has work report locally",
                work_report_hash=work_report_hash.hex()[:16] + "...",
            )
            work_report = wr_storage.get_work_report(work_report_hash)
        else:
            # Step 2: Fetch work report via CE136 if not available
            logger.info(
                "Auditor doesn't have work report, fetching via CE136",
                work_report_hash=work_report_hash.hex()[:16] + "...",
            )

            work_report = await self._fetch_work_report_via_ce136(node, work_report_hash)

            if work_report:
                # Store for future use
                wr_storage.store_work_report(work_report_hash, work_report)
                logger.info(
                    "Work report fetched and stored by auditor",
                    work_report_hash=work_report_hash.hex()[:16] + "...",
                )
            else:
                logger.error(
                    "Failed to fetch work report via CE136",
                    work_report_hash=work_report_hash.hex()[:16] + "...",
                )
                # Create invalid judgment if WR cannot be obtained
                return self._create_judgment_without_wr(
                    epoch_index, validator_index, work_report_hash, validity=False
                )

        # Step 3: Audit the work report to determine validity
        if work_report:
            validity = self._audit_work_report(work_report, work_report_hash)
            logger.info(
                "Auditor completed work report audit",
                work_report_hash=work_report_hash.hex()[:16] + "...",
                validity="valid" if validity else "invalid",
            )
        else:
            # Fallback: if no work report available, mark as invalid
            validity = False
            logger.warning(
                "No work report available for audit, marking as invalid",
                work_report_hash=work_report_hash.hex()[:16] + "...",
            )

        # Step 4: Create and return judgment
        judgment = await self._create_auditor_judgment(
            node, epoch_index, validator_index, work_report_hash, validity
        )

        logger.info(
            "Auditor judgment created successfully",
            epoch_index=epoch_index,
            validator_index=validator_index,
            validity="valid" if validity else "invalid",
            work_report_hash=work_report_hash.hex()[:16] + "...",
        )

        return judgment

    async def _create_auditor_judgment(
        self,
        node,
        epoch_index: int,
        validator_index: int,
        work_report_hash: WorkReportHash,
        validity: bool,
    ) -> Judgment:
        """Create auditor's judgment with proper signature"""

        # Create signature (dummy implementation)
        dummy_sig = b"auditor_judgment_sig_" + f"{validator_index:04d}".encode() + b"0" * 40
        signature = Ed25519Signature(dummy_sig[:64])

        judgment = Judgment(
            epoch_index=epoch_index,
            validator_index=ValidatorIndex(U16(validator_index)),
            validity=U8(1 if validity else 0),
            work_report_hash=work_report_hash,
            signature=signature,
        )

        return judgment

    def _create_judgment_without_wr(
        self,
        epoch_index: int,
        validator_index: int,
        work_report_hash: WorkReportHash,
        validity: bool,
    ) -> Judgment:
        """Create judgment when work report is not available"""

        logger.warning(
            "Creating judgment without work report",
            epoch_index=epoch_index,
            validator_index=validator_index,
            validity=validity,
        )

        # Create signature (dummy implementation)
        dummy_sig = b"no_wr_judgment_sig_" + f"{validator_index:04d}".encode() + b"0" * 40
        signature = Ed25519Signature(dummy_sig[:64])

        judgment = Judgment(
            epoch_index=epoch_index,
            validator_index=ValidatorIndex(U16(validator_index)),
            validity=U8(1 if validity else 0),
            work_report_hash=work_report_hash,
            signature=signature,
        )

        return judgment

    def _should_audit_work_report(self, node: "Node", judgment: Judgment) -> bool:
        """Check if this node should audit the work report"""
        # For now, assume validator nodes should audit
        return hasattr(node, "is_validator") and node.is_validator

    def _audit_work_report(self, work_report, wr_hash: WorkReportHash) -> bool:
        """
        Dummy audit function - always returns True (valid) for now
        TODO: Implement actual work report validation logic
        """
        logger.info(
            "Auditing work report (dummy implementation - always valid)",
            work_report_hash=wr_hash.hex()[:16] + "...",
        )

        # TODO: Implement actual audit logic here
        # For now, always return True (valid)
        # Real implementation would:
        # 1. Validate work report structure
        # 2. Check work execution results
        # 3. Verify cryptographic proofs
        # 4. Return True/False based on validation

        return True  # Always valid for now

    async def _create_own_judgment(
        self, node: QuicPeer, epoch_index: int, wr_hash: WorkReportHash, validity: bool
    ) -> Judgment:
        """Create our own judgment based on audit results"""

        # Create dummy signature
        dummy_sig = b"dummy_judgment_signature_" + b"0" * 38
        signature = Ed25519Signature(dummy_sig[:64])

        # Derive validator index from node (simplified)
        validator_index = ValidatorIndex(U16(hash(b"") % 100))

        judgment = Judgment(
            epoch_index=epoch_index,
            validator_index=validator_index,
            validity=U8(1 if validity else 0),
            work_report_hash=wr_hash,
            signature=signature,
        )

        logger.info(
            "Created own judgment after audit",
            validator_index=int(validator_index),
            validity="valid" if validity else "invalid",
            work_report_hash=wr_hash.hex()[:16] + "...",
        )

        return judgment

    def _store_judgment_for_disputes(self, judgment: Judgment):
        """Store judgment for potential inclusion in disputes extrinsic"""
        logger.debug(
            "Storing judgment for disputes extrinsic inclusion",
            epoch_index=judgment.epoch_index,
            validator_index=int(judgment.validator_index),
            validity=int(judgment.validity),
            work_report_hash=judgment.work_report_hash.hex()[:16] + "...",
        )
        # TODO: Implement actual storage mechanism for block authors

    def res_intercept(self, stream_id: int, client: JAMNP):
        """Intercept acknowledgment (FIN) from Validator"""
        buffer = client.stream_buffer[stream_id]

        if buffer[1:] == b"":
            logger.info("Judgment publication acknowledgment received", stream_id=stream_id)
        else:
            logger.warning(
                "Unexpected response to judgment publication",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )


async def auditor_make_judgment(
    node, epoch_index: int, validator_index: int, work_report_hash: WorkReportHash
) -> Judgment:
    """
    Main function for auditors to create judgments with automatic WR fetching.

    This is the primary entry point auditors should use.

    Args:
        node: The auditor node
        epoch_index: Current epoch index (int)
        validator_index: Auditor's validator index
        work_report_hash: Hash of work report to judge

    Returns:
        Judgment: The auditor's judgment on the work report

    Usage:
        judgment = await auditor_make_judgment(node, epoch, validator_idx, wr_hash)
        ce145_data = create_ce145_data(judgment)
        await ce145_protocol.transmit(node, ce145_data)
    """
    ce145_protocol = JudgmentPublication()
    return await ce145_protocol.auditor_create_judgment(
        node, epoch_index, validator_index, work_report_hash
    )


def create_judgment(
    epoch_index: int,
    validator_index: int,
    validity: bool,
    work_report_hash: WorkReportHash,
    signature: Ed25519Signature = None,
) -> Judgment:
    """
    Utility function to create a judgment.

    Args:
        epoch_index: The epoch index (int type)
        validator_index: Index of the validator making the judgment
        validity: True for valid, False for invalid
        work_report_hash: Hash of the work-report being judged
        signature: Ed25519 signature (creates dummy if None)

    Returns:
        Judgment ready for publication
    """
    if signature is None:
        # Create dummy signature for testing
        dummy_sig = b"dummy_judgment_signature_" + b"0" * 38
        signature = Ed25519Signature(dummy_sig[:64])

    judgment = Judgment(
        epoch_index=epoch_index,
        validator_index=ValidatorIndex(U16(validator_index)),
        validity=U8(1 if validity else 0),
        work_report_hash=work_report_hash,
        signature=signature,
    )

    return judgment


def create_ce145_data(judgment: Judgment) -> CE145Data:
    """
    Utility function to create CE145Data from a judgment.

    Args:
        judgment: The judgment to wrap

    Returns:
        CE145Data ready for transmission
    """
    return CE145Data(len=Uint[32](len(judgment.encode())), judgment=judgment)
