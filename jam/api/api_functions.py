import json
from enum import Enum
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Literal
from jam.assurances.errors import AssurancesError
from jam.report.state import Reporting
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.preimages.preimages import Preimages
from jam.consensus.safrole.safrole import Safrole
from jam.consensus.safrole.errors import SafroleError
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle
from jam.state.utils.state_transformation import GeneralState
from jam.types.extrinsics.assurances import AssurancesExtrinsic
from jam.types.block import Block
from jam.types.extrinsics.disputes import DisputesExtrinsic
from jam.types.block import Extrinsic, Header
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic
from jam.types.extrinsics.preimages import PreimagesExtrinsic
from jam.types.extrinsics.tickets import TicketsExtrinsic
from jam.types.work.refine_context import RefineContext
from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage
from jam.types.work.report import WorkReport
from jam.types.work.report import WorkResult

from jam.api.response_models import (
    SuccessResponse,
    ErrorResponse,
    ConversionSuccessResponse,
    RequestData,
    RequestDataJson,
    RequestDataCodec,
    RequestDataShuffle,
    RequestDataTypes,
    RequestDataCodec,
)


def fetch_type():
    """Fetch available types from type.json file"""
    test_dir = Path(__file__).parent
    type_file_path = test_dir / "examples/type.json"

    if not type_file_path.exists():
        raise FileNotFoundError(f"Example JSON not found at: {type_file_path}")

    with open(test_dir / "examples/type.json", "r") as f:
        type_json = json.load(f)

    return type_json


def export_cases_types():
    """
    Get an overview of all available types.

    Only a subset of types is exposed here for testing. More will follow.
    """
    return fetch_type()


def export_json_to_codec(request_data: RequestDataCodec,
                         type_id: str = Query("assurances_extrinsic", enum=[
                             "assurances_extrinsic",
                             "block",
                             "disputes_extrinsic",
                             "extrinsic",
                             "guarantees_extrinsic",
                             "header",
                             "preimages_extrinsic",
                             "refine_context",
                             "tickets_extrinsic",
                             "work_item",
                             "work_package",
                             "work_report",
                             "work_result"
                         ])):
    """
    Convert JSON data to codec format.

    Takes JSON data and a type label, and returns the hex-encoded codec format.
    """
    try:
        json_file = request_data.input.json_data
        label = type_id

        if label == "assurances_extrinsic":
            assurance = AssurancesExtrinsic.from_json(json_file)
            return {"data": assurance.encode().hex(), "status": "Ok"}

        elif label == "block":
            block = Block.from_json(json_file)
            return {"data": block.encode().hex(), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute = DisputesExtrinsic.from_json(json_file)
            return {"data": dispute.encode().hex(), "status": "Ok"}

        elif label == "extrinsic":
            extrinsic = Extrinsic.from_json(json_file)
            return {"data": extrinsic.encode().hex(), "status": "Ok"}

        elif label == "guarantees_extrinsic":
            guarantee = GuaranteesExtrinsic.from_json(json_file)
            return {"data": guarantee.encode().hex(), "status": "Ok"}

        elif label == "header":
            header = Header.from_json(json_file)
            return {"data": header.encode().hex(), "status": "Ok"}

        elif label == "preimages_extrinsic":
            preimage = PreimagesExtrinsic.from_json(json_file)
            return {"data": preimage.encode().hex(), "status": "Ok"}

        elif label == "refine_context":
            context = RefineContext.from_json(json_file)
            return {"data": context.encode().hex(), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket = TicketsExtrinsic.from_json(json_file)
            return {"data": ticket.encode().hex(), "status": "Ok"}

        elif label == "work_item":
            work_item = WorkItem.from_json(json_file)
            return {"data": work_item.encode().hex(), "status": "Ok"}

        elif label == "work_package":
            work_package = WorkPackage.from_json(json_file)
            return {"data": work_package.encode().hex(), "status": "Ok"}

        elif label == "work_report":
            work_report = WorkReport.from_json(json_file)
            return {"data": work_report.encode().hex(), "status": "Ok"}

        elif label == "work_result":
            work_result = WorkResult.from_json(json_file)
            return {"data": work_result.encode().hex(), "status": "Ok"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


def export_codec_to_json(request_data: RequestDataJson, type_id: str = Query("assurances_extrinsic", enum=[
    "assurances_extrinsic",
    "block",
    "disputes_extrinsic",
    "extrinsic",
    "guarantees_extrinsic",
    "header",
    "preimages_extrinsic",
    "refine_context",
    "tickets_extrinsic",
    "work_item",
    "work_package",
    "work_report",
    "work_result"
])):
    """
    Convert codec data to JSON format.

    Takes hex-encoded codec data and a type label, and returns the JSON representation.
"""
    try:
        label = type_id
        hex_string = request_data.input.codec

        try:
            data = bytes.fromhex(hex_string)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hex string")

        if label == "assurances_extrinsic":
            assurance, _ = AssurancesExtrinsic.decode_from(data)
            return {"data": str(assurance.to_json()), "status": "Ok"}

        elif label == "block":
            block, _ = Block.decode_from(data)
            return {"data": str(block.to_json()), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute, _ = DisputesExtrinsic.decode_from(data)
            return {"data": str(dispute.to_json()), "status": "Ok"}

        elif label == "extrinsic":
            extrinsic, _ = Extrinsic.decode_from(data)
            return {"data": str(extrinsic.to_json()), "status": "Ok"}

        elif label == "guarantees_extrinsic":
            guarantee, _ = GuaranteesExtrinsic.decode_from(data)
            return {"data": str(guarantee.to_json()), "status": "Ok"}

        elif label == "header":
            header, _ = Header.decode_from(data)
            return {"data": str(header.to_json()), "status": "Ok"}

        elif label == "preimages_extrinsic":
            preimage, _ = PreimagesExtrinsic.decode_from(data)
            return {"data": str(preimage.to_json()), "status": "Ok"}

        elif label == "refine_context":
            context, _ = RefineContext.decode_from(data)
            return {"data": str(context.to_json()), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket, _ = TicketsExtrinsic.decode_from(data)
            return {"data": str(ticket.to_json()), "status": "Ok"}

        elif label == "work_item":
            work_item, _ = WorkItem.decode_from(data)
            return {"data": str(work_item.to_json()), "status": "Ok"}

        elif label == "work_package":
            work_package, _ = WorkPackage.decode_from(data)
            return {"data": str(work_package.to_json()), "status": "Ok"}

        elif label == "work_report":
            work_report, _ = WorkReport.decode_from(data)
            return {"data": str(work_report.to_json()), "status": "Ok"}

        elif label == "work_result":
            work_result, _ = WorkResult.decode_from(data)
            return {"data": str(work_result.to_json()), "status": "Ok"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


def export_safrole(request_data: RequestData,
                   type_id: str = Query("non_keyval", enum=[
                       "non_keyval",
                       "keyval"
                   ])):
    """
    Validate state transition according to Safrole consensus.

    Compares the output of the Safrole transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()

        epoch_mark = test_block.header.epoch_mark.value
        if 'none' in epoch_mark:
            entropy = ByteArray32(bytes(32))
        else:
            entropy = test_block.header.epoch_mark.value['some'].entropy

        transition_output = Safrole.transition(test_state, test_block, entropy)

        if request_data.output is None:
            return {"ok": None}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output.tau == output_state.tau, "output_mismatch(tau)"
            assert transition_output.eta[0] == output_state.eta[0], "output_mismatch(eta)"
            assert transition_output.eta[1] == output_state.eta[1], "output_mismatch(eta)"
            assert transition_output.eta[2] == output_state.eta[2], "output_mismatch(eta)"
            assert transition_output.eta[3] == output_state.eta[3], "output_mismatch(eta)"
            assert transition_output.lambda_ == output_state.lambda_, "output_mismatch(lamda)"
            assert transition_output.kappa == output_state.kappa, "output_mismatch(kappa)"
            assert transition_output.gamma.k == output_state.gamma.k, "output_mismatch(gamma_k)"
            assert transition_output.iota == output_state.iota, "output_mismatch(iota)"
            assert transition_output.gamma.a == output_state.gamma.a, "output_mismatch(gamma_a)"
            assert transition_output.gamma.s == output_state.gamma.s, "output_mismatch(gamma_s)"
            assert transition_output.psi.offenders == output_state.psi.offenders, "output_mismatch(psi)"
            # TODO: uncomment this once KZG_commitment(⟦HB⟧) is implemented
            # assert len(transition_output.gamma.z) == len(output_state.gamma_z)
            # assert transition_output.gamma.z == output_state.gamma_z
        except AssertionError as e:
            return JSONResponse(status_code=400, content={"err": str(e)})

        return {"ok": None}

    except SafroleError as e:
        return JSONResponse(status_code=400, content={"err": e.code._value_})
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": "unexpected_error"})


def export_safrole_keyval(request_data: RequestData):
    """
    This function takes pre_state and post_state in key value form
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.parse_keyval_state(request_data.input.state)
        # test_state = GeneralState.parse_keyval_state(request_data.input.state)
        epoch_mark = test_block.header.epoch_mark.value
        if 'none' in epoch_mark:
            entropy = ByteArray32(bytes(32))
        else:
            entropy = test_block.header.epoch_mark.value['some'].entropy

        transition_output = Safrole.transition(test_state, test_block, entropy)

        if request_data.output is None:
            return {"ok": None}
        output_state = GeneralState.parse_keyval_state(request_data.output.state)

        try:
            assert transition_output.tau == output_state.tau, "output_mismatch(tau)"
            assert transition_output.eta[0] == output_state.eta[0], "output_mismatch(eta0)"
            assert transition_output.eta[1] == output_state.eta[1], "output_mismatch(eta1)"
            assert transition_output.eta[2] == output_state.eta[2], "output_mismatch(eta2)"
            assert transition_output.eta[3] == output_state.eta[3], "output_mismatch(eta3)"
            assert transition_output.lambda_ == output_state.lambda_, "output_mismatch(lamda)"
            assert transition_output.kappa == output_state.kappa, "output_mismatch(kappa)"
            assert transition_output.gamma.k == output_state.gamma.k, "output_mismatch(gamma_k)"
            assert transition_output.iota == output_state.iota, "output_mismatch(iota)"
            assert transition_output.gamma.a == output_state.gamma.a, "output_mismatch(gamma_a)"
            assert transition_output.gamma.s == output_state.gamma.s, "output_mismatch(gamma_s)"
            assert transition_output.psi.offenders == output_state.psi.offenders, "output_mismatch(psi)"
            # TODO: uncomment this once KZG_commitment(⟦HB⟧) is implemented
            # assert len(transition_output.gamma.z) == len(output_state.gamma_z)
            # assert transition_output.gamma.z == output_state.gamma_z
        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except SafroleError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_shuffle_validate(request_data: RequestDataShuffle):
    """
    Validate shuffling operation.

    Uses the provided entropy to shuffle the input sequence and returns the result.
    """
    try:
        test_entropy = request_data.input.entropy
        shuffle_sequence = shuffle(test_entropy, request_data.input.input)
        return {"data": shuffle_sequence, "status": "Ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Shuffle failed: {str(e)}")


def export_recent_history(request_data: RequestData):
    """
    Validate state transition according to Recent History rules.

    Compares the output of the Recent History transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = RecentHistory.transition(test_state, test_block, ByteArray32([0] * 32))

        if request_data.output is None:
            return {"ok": None}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        assert transition_output == output_state
    except AssertionError as e:
        return JSONResponse(status_code=400, content={"err": str(e)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


def export_authorization(request_data: RequestData):
    """
    Validate state transition according to Authorization rules.

    Compares the output of the Authorization transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Authorization.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_disputes(request_data: RequestData):
    """
    Validate state transition according to Disputes resolution rules.

    Compares the output of the Disputes transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Disputes.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_assurances(request_data: RequestData):
    """
    Validate state transition according to Assurances rules.

    Compares the output of the Assurances transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Assurances.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()
        try:
            assert transition_output == output_state, "output_mismatch"

        except AssurancesError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssurancesError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_report(request_data: RequestData):
    """
    Validate state transition according to Report rules.

    Compares the output of the Report transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Reporting.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_accumulate(request_data: RequestData):
    """
    Validate state transition according to Accumulation rules.

    Compares the output of the Accumulation transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Accumulation.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_preimages(request_data: RequestData):
    """
    Validate state transition according to Preimages rules.

    Compares the output of the Preimages transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Preimages.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}


def export_statistics(request_data: RequestData):
    """
    Validate state transition according to Statistics rules.

    Compares the output of the Statistics transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Statistics.transition(test_state, test_block)

        if request_data.output is None:
            return {"result": True}

        output_state = GeneralState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output == output_state, "output_mismatch"

        except AssertionError as e:
            return {"err": str(e)}

        return {"ok": None}

    except AssertionError as e:
        return {"err": e.code._value_}
    except Exception as e:
        return {"err": "unexpected_error"}