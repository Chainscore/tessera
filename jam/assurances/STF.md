# Assurances State Transitions

For this STF, we collect assurances first, then process guarantees. 

Assurance {
    anchor = HeaderHash of the block when the WR was taken on-chain
    bitfield = BitArray representing if the core is assuring their availability
    validator_index = Index of Validator assuring
    signature = Signed by validator who is assuring
}

To process assurances:

1. Assurance Anchor (EA.anchor) should be current block's parent hash: https://graypaper.fluffylabs.dev/#/5f542d7/148e00149000

2. EA should be ordered by validator index: https://graypaper.fluffylabs.dev/#/5f542d7/14a10014a900
   
3. Signature should be signed by validator_index and follow this data schema: https://graypaper.fluffylabs.dev/#/5f542d7/14c10014ca00

4. If we have > (2/3)V with assurances, we remove the pending work report: https://graypaper.fluffylabs.dev/#/5f542d7/145d01146301

5. If we have any stale pending WRs, remove them