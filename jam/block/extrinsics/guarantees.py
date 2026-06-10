from jam.block.extrinsics.store import ExtrinsicStore

from jam.models.work.guarantee import (
    GuaranteesExtrinsic,
    ReportGuarantee,
    ValidatorSignature,
    ValidatorSignatures,
)

wrg_store = ExtrinsicStore[ReportGuarantee]()
