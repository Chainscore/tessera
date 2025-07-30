import pytest
from jam.types.protocol.core import TrancheIndex
from jam.types.protocol.crypto import HeaderHash
from jam.storage.tranche_store import (
    Tranche,
    TrancheStore,
    JudgmentRecord,
    tranche_store,
)
from jam.audit.q import sample_work_reports_with_nulls

# Fixtures for dummy data
@pytest.fixture
def dummy_tranche():
    """Returns a dummy Tranche object for testing."""
    return Tranche(tranche_index=TrancheIndex(1), header_hash=HeaderHash(b'header_hash_1'.ljust(32, b'\0')))

@pytest.fixture
def another_dummy_tranche():
    """Returns another dummy Tranche object for testing."""
    return Tranche(tranche_index=TrancheIndex(2), header_hash=HeaderHash(b'header_hash_2'.ljust(32, b'\0')))


def dummy_work_report():
    """Returns a dummy WorkReport object for testing."""
    raw_list = sample_work_reports_with_nulls( "jam/combine.json",total_items=1, null_count=0)
    return raw_list[0]

def another_dummy_work_report():
    """Returns another dummy WorkReport object for testing."""
    raw_list = sample_work_reports_with_nulls( "jam/combine.json",total_items=2, null_count=0)
    return raw_list[1]


@pytest.fixture
def dummy_judgment_record():
    """Returns a dummy JudgmentRecord object for testing."""
    return JudgmentRecord.dummy()

# Test class for TrancheStore
class TestTrancheStore:

    def setup_method(self):
        """Clear the store before each test."""
        tranche_store._tranche_store.clear()

    def test_singleton_instance(self):
        """Tests that the tranche_store is a valid instance of TrancheStore."""
        assert isinstance(tranche_store, TrancheStore)

    def test_add_and_rm_from_unaudited(self, dummy_tranche, dummy_work_report):
        """Tests adding and removing work reports from the unaudited list."""
        # Add
        tranche_store.add_to_unaudited(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert dummy_work_report in state.unaudited_list
        assert len(state.unaudited_list) == 1

        # Add again (should not duplicate)
        tranche_store.add_to_unaudited(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        print("Print bhaiii unaudited",state)
        assert len(state.unaudited_list) == 1

        # Remove
        tranche_store.rm_from_unaudited(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert dummy_work_report not in state.unaudited_list
        assert len(state.unaudited_list) == 0

        # Remove non-existent
        tranche_store.rm_from_unaudited(dummy_tranche, dummy_work_report) # Should not raise error

    def test_update_and_get_judgment(self, dummy_tranche, dummy_work_report, dummy_judgment_record, another_dummy_work_report):
        """Tests updating and retrieving judgments for work reports."""
        # Update
        tranche_store.update_judgment(dummy_tranche, dummy_work_report, dummy_judgment_record)

        # Get
        retrieved_judgment = tranche_store.get_judgment(dummy_tranche, dummy_work_report)
        assert retrieved_judgment is not None
        assert retrieved_judgment == dummy_judgment_record

        # Get non-existent
        assert tranche_store.get_judgment(dummy_tranche, another_dummy_work_report) is None

    def test_add_to_valid_set(self, dummy_tranche, dummy_work_report):
        """Tests adding work reports to the valid set."""
        # Add
        tranche_store.add_to_valid_set(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert dummy_work_report in state.valid_set
        assert len(state.valid_set) == 1

        # Add again (should not duplicate)
        tranche_store.add_to_valid_set(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert len(state.valid_set) == 1

    def test_add_to_invalid_set(self, dummy_tranche, dummy_work_report):
        """Tests adding work reports to the invalid set."""
        # Add
        tranche_store.add_to_invalid_set(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert dummy_work_report in state.invalid_set
        assert len(state.invalid_set) == 1

        # Add again (should not duplicate)
        tranche_store.add_to_invalid_set(dummy_tranche, dummy_work_report)
        state = tranche_store._get_state(dummy_tranche)
        assert len(state.invalid_set) == 1

    def test_delete_tranche(self, dummy_tranche, dummy_work_report):
        """Tests the deletion of a tranche from the store."""
        tranche_store.add_to_unaudited(dummy_tranche, dummy_work_report)
        assert dummy_tranche in tranche_store._tranche_store

        tranche_store.delete_tranche(dummy_tranche)
        assert dummy_tranche not in tranche_store._tranche_store

        # Delete non-existent
        tranche_store.delete_tranche(dummy_tranche) # Should not raise error

    def test_tranche_state_isolation(self, dummy_tranche, another_dummy_tranche, dummy_work_report, another_dummy_work_report):
        """Tests that the states of different tranches are properly isolated."""
        # Add to first tranche
        tranche_store.add_to_unaudited(dummy_tranche, dummy_work_report)

        # Add to second tranche
        tranche_store.add_to_valid_set(another_dummy_tranche, another_dummy_work_report)

        # Check state of first tranche
        state1 = tranche_store._get_state(dummy_tranche)
        assert dummy_work_report in state1.unaudited_list
        assert another_dummy_work_report not in state1.unaudited_list
        assert len(state1.valid_set) == 0

        # Check state of second tranche
        state2 = tranche_store._get_state(another_dummy_tranche)
        assert another_dummy_work_report in state2.valid_set
        assert dummy_work_report not in state2.unaudited_list
        assert len(state2.unaudited_list) == 0
