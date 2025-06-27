import asyncio
from time import time
from typing import Optional, List

from tsrkit_types import U8, U16, U32

from jam.config.logging import get_logger
from jam.network.protocols.ce_145 import JudgmentPublication, Judgment, CE145Data, create_judgment, create_ce145_data
from jam.types.protocol.crypto import Hash, Ed25519Signature, WorkReportHash
from jam.types.protocol.core import ValidatorIndex, EpochIndex

# Module-specific logger
logger = get_logger("judgment")

def create_dummy_signature() -> Ed25519Signature:
    """Create dummy Ed25519 signature for testing"""
    dummy_sig = b"dummy_judgment_signature_" + b"0" * 38  # Make it 64 bytes
    return Ed25519Signature(dummy_sig[:64])

def create_dummy_judgment(
    epoch_index: int = None,
    validator_index: int = None,
    validity: bool = True,
    work_report_hash: WorkReportHash = None,
    signature: Optional[Ed25519Signature] = None
) -> Judgment:
    """
    Create a dummy judgment for testing purposes.

    Args:
        epoch_index: The epoch index (defaults to current time-based epoch)
        validator_index: Index of the validator making the judgment (defaults to 0)
        validity: True for valid, False for invalid (defaults to True)
        work_report_hash: Hash of the work-report (creates dummy if None)
        signature: Ed25519 signature (creates dummy if None)

    Returns:
        Judgment: A dummy judgment ready for publication
    """

    # Use defaults if not provided
    if epoch_index is None:
        epoch_index = int(time()) // 600  # New epoch every 10 minutes for demo

    if validator_index is None:
        validator_index = 0

    if work_report_hash is None:
        # Create dummy work-report hash
        wr_data = f"dummy_work_report_{epoch_index}_{validator_index}_{time()}".encode()
        work_report_hash = Hash.blake2b(wr_data)

    if signature is None:
        signature = create_dummy_signature()

    judgment = create_judgment(
        epoch_index=epoch_index,
        validator_index=validator_index,
        validity=validity,
        work_report_hash=work_report_hash,
        signature=signature
    )

    logger.debug(
        "Created dummy judgment",
        epoch_index=epoch_index,
        validator_index=validator_index,
        validity="valid" if validity else "invalid",
        work_report_hash=work_report_hash.hex()[:16] + "..."
    )

    return judgment

async def publish_judgment(node, judgment: Judgment):
    """
    Publish a judgment using the CE 145 protocol.

    Args:
        node: The network node to use for publishing
        judgment: The judgment to publish
    """
    from jam.network.node import Node

    if not isinstance(node, Node):
        logger.error("Invalid node type provided to publish_judgment")
        return

    if not node.is_validator:
        logger.warning(
            "Node is not a validator - cannot publish judgments",
            node_name=node.name
        )
        return

    logger.info(
        "Publishing judgment via CE 145",
        node_name=node.name,
        epoch_index=int(judgment.epoch_index),
        validator_index=int(judgment.validator_index),
        validity="valid" if judgment.is_valid else "invalid",
        work_report_hash=judgment.work_report_hash.hex()[:16] + "..."
    )

    # Create CE145Data
    ce145_data = create_ce145_data(judgment)

    # Use CE145 protocol to transmit
    ce145 = JudgmentPublication()
    responses = await ce145.transmit(node, ce145_data)

    logger.info(
        "Judgment publication completed",
        node_name=node.name,
        epoch_index=int(judgment.epoch_index),
        response_count=len(responses) if responses else 0
    )

    return responses

async def simulate_auditing_workflow(node):
    """
    Simulate a complete auditing workflow with judgment publication.
    This demonstrates the CE 145 judgment publication protocol.

    Args:
        node: The network node to use for simulation
    """
    from jam.network.node import Node

    if not isinstance(node, Node):
        logger.error("Invalid node type provided to simulate_auditing_workflow")
        return

    if not node.is_validator:
        logger.info(
            "Node is not a validator - skipping auditing simulation",
            node_name=node.name
        )
        return

    logger.info(
        "Starting auditing workflow simulation",
        node_name=node.name
    )

    # Simulate current epoch
    current_epoch = int(time()) // 600  # New epoch every 10 minutes for demo
    validator_index = hash(node.name) % 100  # Derive validator index from name

    # Create dummy work-report hashes to audit
    work_reports = []
    for i in range(3):
        wr_data = f"work_report_{current_epoch}_{i}_{node.name}".encode()
        wr_hash = Hash.blake2b(wr_data)
        work_reports.append(wr_hash)

    logger.info(
        "Simulating audit of work-reports",
        node_name=node.name,
        current_epoch=current_epoch,
        validator_index=validator_index,
        work_report_count=len(work_reports)
    )

    # Process each work-report and create individual judgments
    judgments = []
    for i, wr_hash in enumerate(work_reports):
        logger.info(
            "Processing work-report for audit",
            node_name=node.name,
            work_report_number=i + 1,
            work_report_hash=wr_hash.hex()[:16] + "..."
        )

        # Create individual judgment
        judgment = create_dummy_judgment(
            epoch_index=current_epoch,
            validator_index=validator_index,
            validity=True,  # Always valid for demo
            work_report_hash=wr_hash
        )
        judgments.append(judgment)

        # Publish judgment
        await publish_judgment(node, judgment)

        # Small delay between publications
        await asyncio.sleep(2)

    logger.info(
        "Auditing workflow simulation completed",
        node_name=node.name,
        total_judgments=len(judgments),
        current_epoch=current_epoch
    )

async def judgment_producer(node):
    """
    Continuously produces and publishes individual judgments.
    This simulates an auditor node that periodically audits work-reports
    and publishes individual judgments via CE 145.

    Args:
        node: The network node for communications
    """
    from jam.network.node import Node

    if not isinstance(node, Node):
        logger.error("Invalid node type provided to judgment_producer")
        return

    logger.info(
        "Starting judgment producer",
        node_name=node.name,
        is_validator=node.is_validator
    )

    if not node.is_validator:
        logger.info(
            "Node is not a validator - judgment producer will not run",
            node_name=node.name
        )
        return

    judgment_iter = 0

    while True:
        if not node.is_initialized:
            logger.debug(
                "Network not initialized - skipping judgment production",
                node_name=node.name,
                iteration=judgment_iter
            )
            await asyncio.sleep(10)
            continue

        # Get current epoch
        current_epoch = int(time()) // 600  # New epoch every 10 minutes for demo
        validator_index = hash(node.name) % 100  # Derive validator index from name

        logger.debug(
            "Judgment production cycle",
            node_name=node.name,
            iteration=judgment_iter,
            current_epoch=current_epoch,
            validator_index=validator_index
        )

        # Create a dummy work-report hash to judge
        wr_data = f"work_report_{judgment_iter}_{current_epoch}_{node.name}".encode()
        work_report_hash = Hash.blake2b(wr_data)

        logger.info(
            "Producing judgment for work-report",
            node_name=node.name,
            iteration=judgment_iter,
            work_report_hash=work_report_hash.hex()[:16] + "...",
            epoch_index=current_epoch
        )

        # Create and publish individual judgment
        judgment = create_dummy_judgment(
            epoch_index=current_epoch,
            validator_index=validator_index,
            validity=True,  # Always valid for demo
            work_report_hash=work_report_hash
        )

        await publish_judgment(node, judgment)
        judgment_iter += 1

        # Wait before next judgment (simulate realistic auditing intervals)
        await asyncio.sleep(30)  # 30 seconds between judgments

def create_sample_judgments(node_name: str = "test_node", count: int = 5) -> List[Judgment]:
    """Create a variety of sample judgments for testing."""

    judgments = []
    current_epoch = int(time()) // 600
    validator_index = hash(node_name) % 100

    # Create sample work-report hashes and judgments
    for i in range(count):
        wr_data = f"sample_work_report_{i}_{node_name}_{time()}".encode()
        wr_hash = Hash.blake2b(wr_data)

        # Create mix of valid and invalid judgments for testing
        validity = (i % 4) != 0  # 75% valid, 25% invalid

        judgment = create_dummy_judgment(
            epoch_index=current_epoch,
            validator_index=validator_index,
            validity=validity,
            work_report_hash=wr_hash
        )
        judgments.append(judgment)

    logger.info(
        "Created sample judgments",
        node_name=node_name,
        judgment_count=len(judgments),
        epoch_index=current_epoch,
        valid_count=sum(1 for j in judgments if j.is_valid),
        invalid_count=sum(1 for j in judgments if j.is_invalid)
    )

    return judgments

async def test_judgment_publication(node):
    """
    Test the CE 145 judgment publication protocol with sample data.

    Args:
        node: The network node to use for testing
    """
    from jam.network.node import Node

    if not isinstance(node, Node):
        logger.error("Invalid node type provided to test_judgment_publication")
        return

    logger.info(
        "Testing CE 145 judgment publication protocol",
        node_name=node.name
    )

    # Create sample judgments
    sample_judgments = create_sample_judgments(node.name)

    # Publish each judgment individually
    for i, judgment in enumerate(sample_judgments):
        logger.info(
            "Testing judgment publication",
            node_name=node.name,
            test_number=i + 1,
            total_tests=len(sample_judgments),
            validity="valid" if judgment.is_valid else "invalid",
            work_report_hash=judgment.work_report_hash.hex()[:16] + "..."
        )

        await publish_judgment(node, judgment)
        await asyncio.sleep(3)  # Brief pause between tests

    logger.info(
        "CE 145 judgment publication protocol testing completed",
        node_name=node.name,
        total_tests=len(sample_judgments)
    )

async def simulate_negative_judgment_scenario(node):
    """
    Simulate receiving and handling negative judgments.

    Args:
        node: The network node for simulation
    """
    from jam.network.node import Node

    if not isinstance(node, Node):
        logger.error("Invalid node type provided to simulate_negative_judgment_scenario")
        return

    logger.info(
        "Simulating negative judgment scenario",
        node_name=node.name
    )

    if not node.is_validator:
        logger.info(
            "Node is not a validator - skipping negative judgment simulation",
            node_name=node.name
        )
        return

    # Create negative judgments to simulate the scenario
    current_epoch = int(time()) // 600
    validator_index = hash(node.name) % 100

    # Create work-report hashes for negative judgments
    negative_scenarios = []
    for i in range(2):
        wr_data = f"negative_scenario_{i}_{node.name}_{time()}".encode()
        work_report_hash = Hash.blake2b(wr_data)

        # Create invalid judgment
        judgment = create_dummy_judgment(
            epoch_index=current_epoch,
            validator_index=validator_index,
            validity=False,  # Invalid judgment
            work_report_hash=work_report_hash
        )
        negative_scenarios.append(judgment)

    logger.info(
        "Created negative judgment scenarios",
        node_name=node.name,
        scenario_count=len(negative_scenarios)
    )

    # Publish negative judgments
    for i, judgment in enumerate(negative_scenarios):
        logger.info(
            "Publishing negative judgment",
            node_name=node.name,
            scenario_number=i + 1,
            work_report_hash=judgment.work_report_hash.hex()[:16] + "..."
        )

        await publish_judgment(node, judgment)
        await asyncio.sleep(5)  # Longer pause for negative judgments

    logger.info(
        "Negative judgment scenario simulation completed",
        node_name=node.name
    )

# Main function for standalone testing
async def main():
    """Main function for testing the judgment publication utilities."""
    logger.info("Starting judgment publication utility tests")

    # Create sample judgments for testing
    sample_judgments = create_sample_judgments("test_utility")

    logger.info(
        "Judgment utility test completed",
        sample_count=len(sample_judgments),
        valid_count=sum(1 for j in sample_judgments if j.is_valid),
        invalid_count=sum(1 for j in sample_judgments if j.is_invalid)
    )

if __name__ == "__main__":
    asyncio.run(main())
