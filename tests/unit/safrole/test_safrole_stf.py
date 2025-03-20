from typing import List

from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.consensus.safrole.safrole import Safrole
from jam.types import Boolean
from tests.unit.safrole.types import (
    Testcase,
    get_testcases_starting_with,
)

def vector_transition(vector: Testcase) -> Boolean:
    try:
        # TODO: remove this once vrf verification is implemented
        if vector.output.get_value() == SafroleErrorCode.BAD_TICKET_PROOF:
            return True
        output = Safrole.transition(vector.pre_state.to_state(), vector.input.to_block())
        assert output.tau == vector.post_state.tau
        assert output.eta[0] == vector.post_state.eta[0]
        assert output.eta[1] == vector.post_state.eta[1]
        assert output.eta[2] == vector.post_state.eta[2]
        assert output.eta[3] == vector.post_state.eta[3]
        assert output.lambda_ == vector.post_state.lambda_
        assert output.kappa == vector.post_state.kappa
        assert output.gamma.k == vector.post_state.gamma_k
        assert output.iota == vector.post_state.iota
        assert output.gamma.a == vector.post_state.gamma_a
        assert output.gamma.s == vector.post_state.gamma_s
        assert output.psi.offenders == vector.post_state.post_offenders
        # TODO: uncomment this once KZG_commitment(⟦HB⟧) is implemented
        # assert len(output.gamma.z) == len(vector.post_state.gamma_z)
        # assert output.gamma.z == vector.post_state.gamma_z
    except SafroleError as e:
        assert e.code == vector.output.get_value()

def test_enact_epoch_change_with_no_tickets():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="enact-epoch-change-with-no-tickets"
    )
    for i, vector in enumerate(vectors):
        vector_transition(vector)
        print(f"Passed testcase #{i + 1}")

def test_enact_epoch_change_with_padding():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="enact-epoch-change-with-padding"
    )
    for i, vector in enumerate(vectors):
        vector_transition(vector)
        print(f"Passed testcase #{i + 1}")

def test_publish_tickets_with_mark():
    """Test publishing tickets with mark"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="publish-tickets-with-mark"
    )
    for i, vector in enumerate(vectors):
        vector_transition(vector)
        print(f"Passed testcase #{i + 1}")


def test_publish_tickets_no_mark():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="publish-tickets-no-mark-5"
    )
    for i, vector in enumerate(vectors):
        vector_transition(vector)
        print(f"Passed testcase #{i + 1}")

def test_skip_epoch():
    """Test skipping an epoch"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="skip-epoch"
    )
    for i, vector in enumerate(vectors):
        vector_transition(vector)
        print(f"Passed testcase #{i + 1}")