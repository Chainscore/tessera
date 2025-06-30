from jam.state.state import State


async def sync(final, state: State):

	# Read ts.genesis timestamp
	# Derive curr_slot
	# latest_header = dev-spec["genesis-header"]
	# Till latest_header.slot != curr_slot return
		# Request and import blocks > latest_header
		# latest_header = imported_block

	# Keep reading the latest block every few secs - trigger sync if we're missing blocks
    print("move bitch, ima tryna sync")
