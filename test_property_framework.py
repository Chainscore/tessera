#!/usr/bin/env python3
"""Simple test to verify the property-based testing framework works"""

from tests.unit.disputes.property.strategies import work_report_hash_strategy, disputes_extrinsic_strategy
from tests.unit.disputes.data import create_test_state, create_test_block, MockSignatureContext
from jam.disputes.disputes import Disputes
from jam.disputes.error import DisputesError
import hypothesis.strategies as st

def test_basic_property_framework():
    """Test that the property-based framework can generate and test data"""
    
    print("🧪 Testing property-based framework...")
    
    # Test strategy generation
    print("📊 Generating test data...")
    state = create_test_state()
    
    # Generate multiple examples
    for i in range(5):
        try:
            extrinsic = disputes_extrinsic_strategy().example()
            block = create_test_block(extrinsic)
            
            print(f"Example {i+1}: {len(extrinsic.verdicts)} verdicts, {len(extrinsic.culprits)} culprits, {len(extrinsic.faults)} faults")
            
            with MockSignatureContext(True):
                new_state = Disputes.transition(state, block)
                print(f"  ✅ Succeeded: good={len(new_state.psi.good)}, bad={len(new_state.psi.bad)}, wonky={len(new_state.psi.wonky)}, offenders={len(new_state.psi.offenders)}")
                
        except DisputesError as e:
            print(f"  ⚠️  Expected error: {e.code}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {type(e).__name__}: {e}")
    
    print("✅ Property-based framework test completed!")

if __name__ == "__main__":
    test_basic_property_framework() 