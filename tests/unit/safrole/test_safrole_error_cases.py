import pytest
from jam.state.transitions import SafroleError, SafroleErrorCode
from jam.state.transitions import Safrole
from jam.types.state.eta import Eta
from tsrkit_types.integers import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaP, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from tsrkit_types.bytes import Bytes
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.safrole.data import (
    create_block,
    create_state,
    create_validator_data_from_keys,
    deepcopy,
)


def test_slot_regression_error():
    """Test error when block slot is lower than current state slot"""
    # Create initial state at slot 10
    initial_state = create_state(
        tau=U32(10),
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(
            GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])
        ),
        gamma_z=GammaZ(
            Safrole.compute_ring_root(
                [keys.bandersnatch for keys in create_validator_data_from_keys()]
            )
        ),
        offenders=PsiO([]),
    )

    # Create block with a previous slot
    regression_block = create_block(slot=U32(9), tickets=[])

    # Verify that the transition raises an error
    with pytest.raises(SafroleError) as excinfo:
        Safrole.transition(
            deepcopy(initial_state),
            initial_state,
            regression_block,
            entropy=Bytes[32](create_dummy_bytes(32)),
        )

    assert excinfo.value.code == SafroleErrorCode.BAD_SLOT


def test_invalid_seal_signature():
    """Test error when block has an invalid seal signature"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(
            GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])
        ),
        gamma_z=GammaZ(
            Safrole.compute_ring_root(
                [keys.bandersnatch for keys in create_validator_data_from_keys()]
            )
        ),
        offenders=PsiO([]),
    )

    # Create block with invalid seal
    invalid_seal_block = create_block(slot=U32(6), tickets=[])

    # Verify that the transition raises an error
    # TODO: Uncomment this once the signatures are implemented
    # with pytest.raises(SafroleError) as excinfo:
    Safrole.transition(
        deepcopy(initial_state),
        initial_state,
        invalid_seal_block,
        Bytes[32](create_dummy_bytes(32)),
    )
    # TODO: Uncomment this once the signatures are implemented
    # assert excinfo.value.code == SafroleErrorCode.BAD_TICKET_PROOF
