from jam.config.logging import logger

from jam.utils.constants import (
    MAX_EXPORT_ITEM,
    MAX_IMPORT_ITEM,
    EXTRINSIC_COUNT,
    MAX_ENCODED_WORK_PACKAGE_SIZE,
    SEGMENT_SIZE,
    REFINE_GAS,
    ACCUMULATION_GAS
)

from jam.types.work.item import WorkItem
from jam.types.work.package import  WorkPackage

from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError

class Validator:
    """Functions to validate work package"""

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def export_count(item: WorkItem):
        if item.export_count > MAX_EXPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXPORT_ITEM,
                "count of import segment are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def import_count(item: WorkItem):
        if len(item.import_segments) > MAX_IMPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_IMPORT_ITEM,
                "count of import segment are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def extrinsic_count(item: WorkItem):
        if len(item.extrinsic) > EXTRINSIC_COUNT:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXTRINSIC_COUNT,
                "count of extrinsic more than are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1ad6001a2401?v=0.6.4
    @staticmethod
    def work_package_size(package: WorkPackage):
        auth_token = len(package.authorization)
        parameterization = len(package.authorizer.params)

        extrinsic_len = 0
        item_count = 0

        for x in package.items:
            for y in x.extrinsic:
                extrinsic_len = extrinsic_len + y.len

            item_count = len(x.payload) + len(x.import_segments) * SEGMENT_SIZE + extrinsic_len

        package_size = auth_token + parameterization + item_count
        if package_size > MAX_ENCODED_WORK_PACKAGE_SIZE:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_WORK_PACKAGE_SIZE,
                "count of extrinsic more than are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a2e011a4401?v=0.6.4
    @staticmethod
    def gas_limit(package: WorkPackage):
        total_refine_gas = 0
        total_accumulate_gas = 0
        for x in package.items:
            total_refine_gas = total_refine_gas + x.refine_gas_limit
            total_accumulate_gas = total_accumulate_gas + x.accumulate_gas_limit

        if total_refine_gas >= REFINE_GAS:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_REFINEMENT_GAS,
                "count of extrinsic more than are more than actual value"
            )
        if total_accumulate_gas >= ACCUMULATION_GAS:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_ACCUMULATION_GAS,
                "count of extrinsic more than are more than actual value"
            )

    def validate_wp(self, package: WorkPackage) -> bool:
        try:
            self.work_package_size(package)
            self.gas_limit(package)

            for item in package.items:
                self.export_count(item)
                self.import_count(item)
                self.extrinsic_count(item)

            logger.info("Package Validated Successfully!")

            return True

        except WorkPackageError as err:
            logger.info(f"WP Validation failed! Error {err.code}: {err.message}")
            return False