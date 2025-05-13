from jam.network.protocols.base import PrefixType
from jam.network.protocols.ce_133 import WorkPackageSubmission
from jam.network.protocols.ce_134 import WorkPackageSharing
from jam.network.protocols.ce_135 import WorkReportDistribution
from jam.network.protocols.ce_136 import WorkReportRequest
from jam.network.protocols.ce_139 import SegmentShardRequest
from jam.network.protocols.ce_140 import SegmentShardRequestWithJustifications

from jam.network.protocols.up_0 import BlockAnnouncement
from jam.network.protocols.ce_137 import ShardDistributionProtocol
from jam.network.protocols.ce_138 import AuditShardRequestProtocol

class ProtocolMap:
    ALL_PROTOCOLS = {
        PrefixType.UP0: BlockAnnouncement,
        PrefixType.CE133: WorkPackageSubmission,
        PrefixType.CE134: WorkPackageSharing,
        PrefixType.CE135: WorkReportDistribution,
        PrefixType.CE136: WorkReportRequest,
        PrefixType.CE137: ShardDistributionProtocol,
        PrefixType.CE138: AuditShardRequestProtocol,
        PrefixType.CE139: SegmentShardRequest,
        PrefixType.CE140: SegmentShardRequestWithJustifications
    }

    @classmethod
    def get_protocol(cls, prefix: PrefixType):
        protocol = cls.ALL_PROTOCOLS.get(prefix)

        if protocol is None:
            raise ConnectionError("Unknown Protocol Call received!")

        return protocol