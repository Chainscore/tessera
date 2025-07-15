from jam.network.base.protocol import PrefixType
from jam.network.protocols.ce_128 import BlockRequest
from jam.network.protocols.ce_131 import SafroleTicketDistribution
from jam.network.protocols.ce_133 import WorkPackageSubmission
from jam.network.protocols.ce_134 import WorkPackageSharing
from jam.network.protocols.ce_135 import WorkReportDistribution
from jam.network.protocols.ce_136 import WorkReportRequest
from jam.network.protocols.ce_139 import SegmentShardRequest
from jam.network.protocols.ce_140 import SegmentShardRequestWithJustifications
from jam.network.protocols.ce_141 import AssuranceDistribution
from jam.network.protocols.ce_145 import JudgmentPublication
from jam.network.protocols.ce_201 import GhostProtocol
from jam.network.protocols.up_0 import BlockAnnouncement
from jam.network.protocols.ce_137 import ShardDistributionProtocol
from jam.network.protocols.ce_138 import AuditShardRequestProtocol


class ProtocolMap:
    """mapping for all the protocols"""

    ALL_PROTOCOLS = {
        PrefixType.UP0: BlockAnnouncement,
        PrefixType.CE128: BlockRequest,
        PrefixType.CE129: GhostProtocol,
        PrefixType.CE130: GhostProtocol,
        PrefixType.CE131: SafroleTicketDistribution,
        PrefixType.CE132: GhostProtocol,
        PrefixType.CE133: WorkPackageSubmission,
        PrefixType.CE134: WorkPackageSharing,
        PrefixType.CE135: WorkReportDistribution,
        PrefixType.CE136: WorkReportRequest,
        PrefixType.CE137: ShardDistributionProtocol,
        PrefixType.CE138: AuditShardRequestProtocol,
        PrefixType.CE139: SegmentShardRequest,
        PrefixType.CE140: SegmentShardRequestWithJustifications,
        PrefixType.CE141: AssuranceDistribution,
        PrefixType.CE145: JudgmentPublication,
        PrefixType.CE201: GhostProtocol,
    }

    @classmethod
    def get_protocol(cls, prefix: PrefixType):
        protocol = cls.ALL_PROTOCOLS.get(prefix)

        if protocol is None:
            raise ConnectionError("Unknown Protocol Call received!")

        return protocol
