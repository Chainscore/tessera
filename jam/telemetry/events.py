"""
JIP-3 Event Type Definitions for jamtart telemetry.

Based on the JAM Telemetry Protocol specification (JIP-3).
Uses @structure from tsrkit-types for native encoding support.
"""
from typing import Optional, List
from tsrkit_types import structure, U8, U16, U32, U64, String, Bytes32, Bytes64, Option, Bytes, Bool
from tsrkit_types.sequences import TypedVector
from jam.utils.constants import C

# Common Types
Slot = U32
EpochIndex = U32
ValidatorIndex = U16
CoreIndex = U16
ServiceId = U32
ShardIndex = U16
Hash = Bytes32
HeaderHash = Bytes32
WorkPackageHash = Bytes32
WorkReportHash = Bytes32
ErasureRoot = Bytes32
SegmentsRoot = Bytes32
Ed25519Signature = Bytes64
PeerId = Bytes32

class Event:
    """Base class for all telemetry events"""
    DISCRIMINATOR = U8(255)


# -----------------------------------------------------------------------------
# Meta Events
# -----------------------------------------------------------------------------

@structure
class Dropped(Event):
    """Event 0: Dropped"""
    DISCRIMINATOR = U8(0)
    count: U64

# -----------------------------------------------------------------------------
# Status Events
# -----------------------------------------------------------------------------

@structure
class Status(Event):
    """Event 10: Status"""
    DISCRIMINATOR = U8(10)
    num_peers: U32
    num_validator_peers: U32
    num_block_announcement_peers: U32
    guarantees_by_core: Bytes(C)  # [u8; C]
    num_shards: U32
    shards_size: U64
    num_preimages: U32
    preimages_size: U32

@structure
class BestBlockChanged(Event):
    """Event 11: Best block changed"""
    DISCRIMINATOR = U8(11)
    slot: Slot
    hash: HeaderHash

@structure
class FinalizedBlockChanged(Event):
    """Event 12: Finalized block changed"""
    DISCRIMINATOR = U8(12)
    slot: Slot
    hash: HeaderHash

@structure
class SyncStatusChanged(Event):
    """Event 13: Sync status changed"""
    DISCRIMINATOR = U8(13)
    synced: Bool

# -----------------------------------------------------------------------------
# Networking Events
# -----------------------------------------------------------------------------

@structure
class PeerAddress:
    ip: Bytes(16)
    port: U16

@structure
class ConnectionRefused(Event):
    """Event 20: Connection refused"""
    DISCRIMINATOR = U8(20)
    address: PeerAddress

@structure
class ConnectingIn(Event):
    """Event 21: Connecting in"""
    DISCRIMINATOR = U8(21)
    address: PeerAddress

@structure
class ConnectInFailed(Event):
    """Event 22: Connect in failed"""
    DISCRIMINATOR = U8(22)
    event_id: U64
    reason: String

@structure
class ConnectedIn(Event):
    """Event 23: Connected in"""
    DISCRIMINATOR = U8(23)
    event_id: U64
    peer_id: PeerId

@structure
class ConnectingOut(Event):
    """Event 24: Connecting out"""
    DISCRIMINATOR = U8(24)
    peer_id: PeerId
    address: PeerAddress

@structure
class ConnectOutFailed(Event):
    """Event 25: Connect out failed"""
    DISCRIMINATOR = U8(25)
    event_id: U64
    reason: String

@structure
class ConnectedOut(Event):
    """Event 26: Connected out"""
    DISCRIMINATOR = U8(26)
    event_id: U64

@structure
class Disconnected(Event):
    """Event 27: Disconnected"""
    DISCRIMINATOR = U8(27)
    peer_id: PeerId
    terminator: Option[U8] # 0 = Local, 1 = Remote
    reason: String

@structure
class PeerMisbehaved(Event):
    """Event 28: Peer misbehaved"""
    DISCRIMINATOR = U8(28)
    peer_id: PeerId
    reason: String

# -----------------------------------------------------------------------------
# Block Authoring/Importing Events
# -----------------------------------------------------------------------------

@structure
class BlockOutline:
    size: U32
    header_hash: HeaderHash
    num_tickets: U32
    num_preimages: U32
    preimages_size: U32
    num_guarantees: U32
    num_assurances: U32
    num_disputes: U32

@structure
class ExecCost:
    gas: U64
    wall_clock_ns: U64

@structure
class AccumulateCost:
    num_accumulate_calls: U32
    num_transfers: U32
    num_items: U32
    total_exec: ExecCost
    load_compile_ns: U64
    read_write_exec: ExecCost
    lookup_exec: ExecCost
    query_solicit_forget_provide_exec: ExecCost
    info_new_upgrade_eject_exec: ExecCost
    transfer_exec: ExecCost
    transfer_gas: U64
    other_exec: ExecCost

@structure
class ServiceExecution:
    service_id: ServiceId
    cost: AccumulateCost

@structure
class Authoring(Event):
    """Event 40: Authoring"""
    DISCRIMINATOR = U8(40)
    slot: Slot
    parent_hash: HeaderHash

@structure
class AuthoringFailed(Event):
    """Event 41: Authoring failed"""
    DISCRIMINATOR = U8(41)
    event_id: U64
    reason: String

@structure
class Authored(Event):
    """Event 42: Authored"""
    DISCRIMINATOR = U8(42)
    event_id: U64
    block: BlockOutline

@structure
class Importing(Event):
    """Event 43: Importing"""
    DISCRIMINATOR = U8(43)
    slot: Slot
    block: BlockOutline

@structure
class BlockVerificationFailed(Event):
    """Event 44: Block verification failed"""
    DISCRIMINATOR = U8(44)
    event_id: U64
    reason: String

@structure
class BlockVerified(Event):
    """Event 45: Block verified"""
    DISCRIMINATOR = U8(45)
    event_id: U64

@structure
class BlockExecutionFailed(Event):
    """Event 46: Block execution failed"""
    DISCRIMINATOR = U8(46)
    event_id: U64
    reason: String

@structure
class BlockExecuted(Event):
    """Event 47: Block executed"""
    DISCRIMINATOR = U8(47)
    event_id: U64
    services: TypedVector[ServiceExecution]

# -----------------------------------------------------------------------------
# Block Distribution Events
# -----------------------------------------------------------------------------

@structure
class BlockAnnouncementStreamOpened(Event):
    """Event 60"""
    DISCRIMINATOR = U8(60)
    peer_id: PeerId
    side: U8 # 0=Local, 1=Remote

@structure
class BlockAnnouncementStreamClosed(Event):
    """Event 61"""
    DISCRIMINATOR = U8(61)
    peer_id: PeerId
    side: U8
    reason: String

@structure
class BlockAnnounced(Event):
    """Event 62"""
    DISCRIMINATOR = U8(62)
    peer_id: PeerId
    announcer: U8 # 0=Local, 1=Remote
    slot: Slot
    header_hash: HeaderHash

@structure
class SendingBlockRequest(Event):
    """Event 63"""
    DISCRIMINATOR = U8(63)
    peer_id: PeerId
    header_hash: HeaderHash
    direction: U8 # 0=Ascending, 1=Descending
    max_blocks: U32

@structure
class ReceivingBlockRequest(Event):
    """Event 64"""
    DISCRIMINATOR = U8(64)
    peer_id: PeerId

@structure
class BlockRequestFailed(Event):
    """Event 65"""
    DISCRIMINATOR = U8(65)
    event_id: U64
    reason: String

@structure
class BlockRequestSent(Event):
    """Event 66"""
    DISCRIMINATOR = U8(66)
    event_id: U64

@structure
class BlockRequestReceived(Event):
    """Event 67"""
    DISCRIMINATOR = U8(67)
    event_id: U64
    header_hash: HeaderHash
    direction: U8
    max_blocks: U32

@structure
class BlockTransferred(Event):
    """Event 68"""
    DISCRIMINATOR = U8(68)
    event_id: U64
    slot: Slot
    block: BlockOutline
    last_block: Bool

# -----------------------------------------------------------------------------
# Safrole Ticket Events
# -----------------------------------------------------------------------------

@structure
class GeneratingTickets(Event):
    """Event 80"""
    DISCRIMINATOR = U8(80)
    epoch: EpochIndex

@structure
class TicketGenerationFailed(Event):
    """Event 81"""
    DISCRIMINATOR = U8(81)
    event_id: U64
    reason: String

@structure
class TicketsGenerated(Event):
    """Event 82"""
    DISCRIMINATOR = U8(82)
    event_id: U64
    tickets: TypedVector[Bytes32]

@structure
class TicketTransferFailed(Event):
    """Event 83"""
    DISCRIMINATOR = U8(83)
    peer_id: PeerId
    sender: U8
    is_ce132: Bool
    reason: String

@structure
class TicketTransferred(Event):
    """Event 84"""
    DISCRIMINATOR = U8(84)
    peer_id: PeerId
    sender: U8
    is_ce132: Bool
    epoch: EpochIndex
    attempt: U8
    vrf_output: Bytes32

# -----------------------------------------------------------------------------
# Guaranteeing Events
# -----------------------------------------------------------------------------

@structure
class IsAuthorizedCost:
    total: ExecCost
    load_compile_ns: U64
    host_calls: ExecCost

@structure
class RefineCost:
    total: ExecCost
    load_compile_ns: U64
    lookup: ExecCost
    machine: ExecCost
    peek_poke: ExecCost
    invoke: ExecCost
    other: ExecCost

@structure
class ImportSpec:
    root: Bytes32 # Root Identifier
    export_index: U16

@structure
class WorkItemOutline:
    service_id: ServiceId
    payload_size: U32
    refine_gas: U64
    accumulate_gas: U64
    extrinsic_len: U32
    imports: TypedVector[ImportSpec]
    num_exports: U16

@structure
class WorkPackageOutline:
    size: U32
    hash: WorkPackageHash
    anchor_hash: HeaderHash
    anchor_slot: Slot
    prerequisites: TypedVector[WorkPackageHash]
    items: TypedVector[WorkItemOutline]

@structure
class WorkReportOutline:
    hash: WorkReportHash
    bundle_size: U32
    erasure_root: ErasureRoot
    segments_root: SegmentsRoot

@structure
class GuaranteeOutline:
    work_report_hash: WorkReportHash
    slot: Slot
    guarantors: TypedVector[ValidatorIndex]

@structure
class WorkPackageSubmission(Event):
    """Event 90"""
    DISCRIMINATOR = U8(90)
    peer_id: PeerId
    is_ce146: Bool

@structure
class WorkPackageBeingShared(Event):
    """Event 91"""
    DISCRIMINATOR = U8(91)
    peer_id: PeerId

@structure
class WorkPackageFailed(Event):
    """Event 92"""
    DISCRIMINATOR = U8(92)
    event_id: U64
    reason: String

@structure
class DuplicateWorkPackage(Event):
    """Event 93"""
    DISCRIMINATOR = U8(93)
    event_id: U64
    core: CoreIndex
    hash: WorkPackageHash

@structure
class WorkPackageReceived(Event):
    """Event 94"""
    DISCRIMINATOR = U8(94)
    event_id: U64
    core: CoreIndex
    outline: WorkPackageOutline

@structure
class Authorized(Event):
    """Event 95"""
    DISCRIMINATOR = U8(95)
    event_id: U64
    cost: IsAuthorizedCost

@structure
class ExtrinsicDataReceived(Event):
    """Event 96"""
    DISCRIMINATOR = U8(96)
    event_id: U64

@structure
class ImportsReceived(Event):
    """Event 97"""
    DISCRIMINATOR = U8(97)
    event_id: U64
    
@structure
class SharingWorkPackage(Event):
    """Event 98"""
    DISCRIMINATOR = U8(98)
    event_id: U64
    peer_id: PeerId

@structure
class WorkPackageSharingFailed(Event):
    """Event 99"""
    DISCRIMINATOR = U8(99)
    event_id: U64
    peer_id: PeerId
    reason: String

@structure
class BundleSent(Event):
    """Event 100"""
    DISCRIMINATOR = U8(100)
    event_id: U64
    peer_id: PeerId

@structure
class Refined(Event):
    """Event 101"""
    DISCRIMINATOR = U8(101)
    event_id: U64
    costs: TypedVector[RefineCost]

@structure
class WorkReportBuilt(Event):
    """Event 102"""
    DISCRIMINATOR = U8(102)
    event_id: U64
    outline: WorkReportOutline

@structure
class WorkReportSignatureSent(Event):
    """Event 103"""
    DISCRIMINATOR = U8(103)
    event_id: U64

@structure
class WorkReportSignatureReceived(Event):
    """Event 104"""
    DISCRIMINATOR = U8(104)
    event_id: U64
    peer_id: PeerId

@structure
class GuaranteeBuilt(Event):
    """Event 105"""
    DISCRIMINATOR = U8(105)
    event_id: U64
    outline: GuaranteeOutline

@structure
class SendingGuarantee(Event):
    """Event 106"""
    DISCRIMINATOR = U8(106)
    event_id: U64
    peer_id: PeerId

@structure
class GuaranteeSendFailed(Event):
    """Event 107"""
    DISCRIMINATOR = U8(107)
    event_id: U64
    reason: String

@structure
class GuaranteeSent(Event):
    """Event 108"""
    DISCRIMINATOR = U8(108)
    event_id: U64

@structure
class GuaranteesDistributed(Event):
    """Event 109"""
    DISCRIMINATOR = U8(109)
    event_id: U64

@structure
class ReceivingGuarantee(Event):
    """Event 110"""
    DISCRIMINATOR = U8(110)
    peer_id: PeerId

@structure
class GuaranteeReceiveFailed(Event):
    """Event 111"""
    DISCRIMINATOR = U8(111)
    event_id: U64
    reason: String

@structure
class GuaranteeReceived(Event):
    """Event 112"""
    DISCRIMINATOR = U8(112)
    event_id: U64
    outline: GuaranteeOutline

@structure
class GuaranteeDiscarded(Event):
    """Event 113"""
    DISCRIMINATOR = U8(113)
    outline: GuaranteeOutline
    reason: U8

# -----------------------------------------------------------------------------
# Availability Distribution Events
# -----------------------------------------------------------------------------

@structure
class SendingShardRequest(Event):
    """Event 120"""
    DISCRIMINATOR = U8(120)
    peer_id: PeerId
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@structure
class ReceivingShardRequest(Event):
    """Event 121"""
    DISCRIMINATOR = U8(121)
    peer_id: PeerId

@structure
class ShardRequestFailed(Event):
    """Event 122"""
    DISCRIMINATOR = U8(122)
    event_id: U64
    reason: String

@structure
class ShardRequestSent(Event):
    """Event 123"""
    DISCRIMINATOR = U8(123)
    event_id: U64

@structure
class ShardRequestReceived(Event):
    """Event 124"""
    DISCRIMINATOR = U8(124)
    event_id: U64
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@structure
class ShardsTransferred(Event):
    """Event 125"""
    DISCRIMINATOR = U8(125)
    event_id: U64

@structure
class DistributingAssurance(Event):
    """Event 126"""
    DISCRIMINATOR = U8(126)
    anchor: HeaderHash
    bitfield: Bytes((C + 7) // 8)

@structure
class AssuranceSendFailed(Event):
    """Event 127"""
    DISCRIMINATOR = U8(127)
    event_id: U64
    peer_id: PeerId
    reason: String

@structure
class AssuranceSent(Event):
    """Event 128"""
    DISCRIMINATOR = U8(128)
    event_id: U64
    peer_id: PeerId

@structure
class AssuranceDistributed(Event):
    """Event 129"""
    DISCRIMINATOR = U8(129)
    event_id: U64

@structure
class AssuranceReceiveFailed(Event):
    """Event 130"""
    DISCRIMINATOR = U8(130)
    peer_id: PeerId
    reason: String

@structure
class AssuranceReceived(Event):
    """Event 131"""
    DISCRIMINATOR = U8(131)
    peer_id: PeerId
    anchor: HeaderHash

# -----------------------------------------------------------------------------
# Bundle Recovery Events
# -----------------------------------------------------------------------------

@structure
class SendingBundleShardRequest(Event):
    """Event 140"""
    DISCRIMINATOR = U8(140)
    event_id: U64
    peer_id: PeerId
    shard_index: ShardIndex

@structure
class ReceivingBundleShardRequest(Event):
    """Event 141"""
    DISCRIMINATOR = U8(141)
    peer_id: PeerId

@structure
class BundleShardRequestFailed(Event):
    """Event 142"""
    DISCRIMINATOR = U8(142)
    event_id: U64
    reason: String

@structure
class BundleShardRequestSent(Event):
    """Event 143"""
    DISCRIMINATOR = U8(143)
    event_id: U64

@structure
class BundleShardRequestReceived(Event):
    """Event 144"""
    DISCRIMINATOR = U8(144)
    event_id: U64
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@structure
class BundleShardTransferred(Event):
    """Event 145"""
    DISCRIMINATOR = U8(145)
    event_id: U64

@structure
class ReconstructingBundle(Event):
    """Event 146"""
    DISCRIMINATOR = U8(146)
    event_id: U64
    is_trivial: Bool

@structure
class BundleReconstructed(Event):
    """Event 147"""
    DISCRIMINATOR = U8(147)
    event_id: U64

@structure
class SendingBundleRequest(Event):
    """Event 148"""
    DISCRIMINATOR = U8(148)
    event_id: U64
    peer_id: PeerId

@structure
class ReceivingBundleRequest(Event):
    """Event 149"""
    DISCRIMINATOR = U8(149)
    peer_id: PeerId

@structure
class BundleRequestFailed(Event):
    """Event 150"""
    DISCRIMINATOR = U8(150)
    event_id: U64
    reason: String

@structure
class BundleRequestSent(Event):
    """Event 151"""
    DISCRIMINATOR = U8(151)
    event_id: U64

@structure
class BundleRequestReceived(Event):
    """Event 152"""
    DISCRIMINATOR = U8(152)
    event_id: U64
    erasure_root: ErasureRoot

@structure
class BundleTransferred(Event):
    """Event 153"""
    DISCRIMINATOR = U8(153)
    event_id: U64

# -----------------------------------------------------------------------------
# Segment Recovery Events
# -----------------------------------------------------------------------------

@structure
class WorkPackageHashMapped(Event):
    """Event 160"""
    DISCRIMINATOR = U8(160)
    event_id: U64
    wp_hash: WorkPackageHash
    segments_root: SegmentsRoot

@structure
class SegmentsRootMapped(Event):
    """Event 161"""
    DISCRIMINATOR = U8(161)
    event_id: U64
    segments_root: SegmentsRoot
    erasure_root: ErasureRoot

@structure
class SegmentShardRequest(Event):
    """Helper struct for event 162"""
    segment_id: U16
    shard_index: ShardIndex

@structure
class SendingSegmentShardRequest(Event):
    """Event 162"""
    DISCRIMINATOR = U8(162)
    event_id: U64
    peer_id: PeerId
    is_ce140: Bool
    shards: TypedVector[SegmentShardRequest]

@structure
class ReceivingSegmentShardRequest(Event):
    """Event 163"""
    DISCRIMINATOR = U8(163)
    peer_id: PeerId
    is_ce140: Bool

@structure
class SegmentShardRequestFailed(Event):
    """Event 164"""
    DISCRIMINATOR = U8(164)
    event_id: U64
    reason: String

@structure
class SegmentShardRequestSent(Event):
    """Event 165"""
    DISCRIMINATOR = U8(165)
    event_id: U64

@structure
class SegmentShardRequestReceived(Event):
    """Event 166"""
    DISCRIMINATOR = U8(166)
    event_id: U64
    num_shards: U16

@structure
class SegmentShardsTransferred(Event):
    """Event 167"""
    DISCRIMINATOR = U8(167)
    event_id: U64

@structure
class ReconstructingSegments(Event):
    """Event 168"""
    DISCRIMINATOR = U8(168)
    event_id: U64
    segments: TypedVector[U16] # Import Segment ID
    is_trivial: Bool

@structure
class SegmentReconstructionFailed(Event):
    """Event 169"""
    DISCRIMINATOR = U8(169)
    event_id: U64
    reason: String

@structure
class SegmentsReconstructed(Event):
    """Event 170"""
    DISCRIMINATOR = U8(170)
    event_id: U64

@structure
class SegmentVerificationFailed(Event):
    """Event 171"""
    DISCRIMINATOR = U8(171)
    event_id: U64
    failed_indices: TypedVector[U16]
    reason: String

@structure
class SegmentsVerified(Event):
    """Event 172"""
    DISCRIMINATOR = U8(172)
    event_id: U64
    verified_indices: TypedVector[U16]

@structure
class SendingSegmentRequest(Event):
    """Event 173"""
    DISCRIMINATOR = U8(173)
    event_id: U64
    peer_id: PeerId
    segments: TypedVector[U16]

@structure
class ReceivingSegmentRequest(Event):
    """Event 174"""
    DISCRIMINATOR = U8(174)
    peer_id: PeerId

@structure
class SegmentRequestFailed(Event):
    """Event 175"""
    DISCRIMINATOR = U8(175)
    event_id: U64
    reason: String

@structure
class SegmentRequestSent(Event):
    """Event 176"""
    DISCRIMINATOR = U8(176)
    event_id: U64

@structure
class SegmentRequestReceived(Event):
    """Event 177"""
    DISCRIMINATOR = U8(177)
    event_id: U64
    num_segments: U16

@structure
class SegmentsTransferred(Event):
    """Event 178"""
    DISCRIMINATOR = U8(178)
    event_id: U64

# -----------------------------------------------------------------------------
# Preimage Distribution Events
# -----------------------------------------------------------------------------

@structure
class PreimageAnnouncementFailed(Event):
    """Event 190"""
    DISCRIMINATOR = U8(190)
    peer_id: PeerId
    announcer: U8
    reason: String

@structure
class PreimageAnnounced(Event):
    """Event 191"""
    DISCRIMINATOR = U8(191)
    peer_id: PeerId
    announcer: U8
    service_id: ServiceId
    hash: Hash
    length: U32

@structure
class AnnouncedPreimageForgotten(Event):
    """Event 192"""
    DISCRIMINATOR = U8(192)
    service_id: ServiceId
    hash: Hash
    length: U32
    reason: U8

@structure
class SendingPreimageRequest(Event):
    """Event 193"""
    DISCRIMINATOR = U8(193)
    peer_id: PeerId
    hash: Hash

@structure
class ReceivingPreimageRequest(Event):
    """Event 194"""
    DISCRIMINATOR = U8(194)
    peer_id: PeerId

@structure
class PreimageRequestFailed(Event):
    """Event 195"""
    DISCRIMINATOR = U8(195)
    event_id: U64
    reason: String

@structure
class PreimageRequestSent(Event):
    """Event 196"""
    DISCRIMINATOR = U8(196)
    event_id: U64

@structure
class PreimageRequestReceived(Event):
    """Event 197"""
    DISCRIMINATOR = U8(197)
    event_id: U64
    hash: Hash

@structure
class PreimageTransferred(Event):
    """Event 198"""
    DISCRIMINATOR = U8(198)
    event_id: U64
    length: U32

@structure
class PreimageDiscarded(Event):
    """Event 199"""
    DISCRIMINATOR = U8(199)
    hash: Hash
    length: U32
    reason: U8
