
from jam.state.merkle.merkle import StateTrie


def visualize_trie(trie: StateTrie) -> str:
    """Visualize the trie as a tree structure in ASCII art."""
    result = []
    
    def format_hex(hex_str: str) -> str:
        """Format a hex string for display (truncate if too long)."""
        hex_str=str(hex_str)
        if hex_str == 'None':
            return 'None'
        if hex_str == '0x0000000000000000000000000000000000000000000000000000000000000000':
            return '0...0'  # Special case for all zeros
        return hex_str[2:10] + '...' + hex_str[-4:]
    
    def traverse(node_id: str, prefix: str, is_last: bool, depth: int = 0) -> None:
        """Recursively traverse the trie to build the visualization."""
        if node_id not in trie.nodes and node_id != '0x0000000000000000000000000000000000000000000000000000000000000000':
            result.append(f"{prefix}{'└── ' if is_last else '├── '}{format_hex(node_id)} (leaf)")
            return
        
        node = trie.nodes.get(node_id)
        
        # For the special null node case
        if node_id == '0x0000000000000000000000000000000000000000000000000000000000000000':
            result.append(f"{prefix}{'└── ' if is_last else '├── '}0x0...0 (null)")
            return
        
        # Add this node to the result
        node_info = f"lvl={node.bit_index}"
        result.append(f"{prefix}{'└── ' if is_last else '├── '}{format_hex(node_id)} [{node_info}]")
        
        if node.left is None and node.right is None:
            encoded_short = format_hex(node.encoded)
            result.append(f"{prefix}{'    ' if is_last else '│   '}└── encoded={encoded_short}")
            return
        
        # Process children
        new_prefix = prefix + ('    ' if is_last else '│   ')
        
        # Process left child if it exists
        if node.left is not None:
            traverse(node.left, new_prefix, node.right is None, depth + 1)
        
        # Process right child if it exists
        if node.right is not None:
            traverse(node.right, new_prefix, True, depth + 1)
    
    # Start traversal from root
    result.append("\n")
    result.append(f"StateTrie Root: {format_hex(trie.root_hash)}")
    if trie.root_hash in trie.nodes:
        traverse(trie.root_hash, "", True)
    result.append("\n──────────────────────────")
    return '\n'.join(result)
