import asyncio
from pathlib import Path
from typing import List, Optional, Dict

from jam.api.rpc.subscription_handlers import subscribe_best_block
from jam.block import Block
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import OpaqueHash, HeaderHash

from tsrkit_types import Dictionary, Enum, structure, Option, TypedVector

from rockstore import RockStore


class BlockStatus(Enum):
    audited = "audited"
    unaudited = "unaudited"
    final = "final"
    invalid = "invalid"

@structure
class BlockMeta:
    slot: TimeSlot
    header: HeaderHash
    status: BlockStatus

Heads = TypedVector[OpaqueHash]

class GhostBlock:
    slot: TimeSlot = TimeSlot(0)
    parent: Optional["GhostBlock"] = None
    children: List["GhostBlock"] = []
    header: HeaderHash = HeaderHash(32)
    status: BlockStatus = BlockStatus.final

    def to_meta(self):
        return BlockMeta(
            self.slot,
            self.header,
            self.status
        )

    def __repr__(self):
        return f"GhostBlock(header={self.header.hex()}, slot={self.slot}, status={self.status.value})"

    def __init__ (self, block: Optional[Block], parent: Optional["GhostBlock"] = None):
        self.status = BlockStatus("unaudited")
        if block is None:
            block = Block.genesis()
            self.status = BlockStatus("final")

        self.header = block.header.hash()
        self.slot = block.header.slot
        self.children = TypedVector[GhostBlock]([])
        self.parent = parent

        if parent is not None:
            parent.children.append(self)
            if len(parent.children) > 1:
                print("FORK DETECTED AT BLOCK", parent.header.hex())

    def detach_from_parent(self):
        if self.parent:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
            self.parent = None

class BlockView:
    final: Optional[GhostBlock]
    heads: Heads
    best: Optional[GhostBlock]

    _index_map: Dict[HeaderHash, GhostBlock]

    def __init__(self):
        self.final = None
        self.heads = Heads([])
        self.acceptable = []
        self.best = None

        # map Header Hash -> GhostBlock for quick lookup
        self._index_map = dict[HeaderHash, GhostBlock]({})

    def initialize(self, kv: RockStore):
        self._index_map = {}
        from jam.finality.finality import Finality

        latest_heads = Finality.load_heads(kv)
        final_block = Finality.load_final(kv)

        ghost_final = GhostBlock(final_block)
        self.final = ghost_final
        self._index_map[final_block.header.hash()] = ghost_final
        ghost_final.status = BlockStatus("final")

        if (isinstance(latest_heads, Block) or
                (len(latest_heads) == 1 and latest_heads[0] == ghost_final.header)
        ):
            self.heads = Heads([ghost_final.header])

        else:
            print("LATEST HEADS", latest_heads)
            for head in latest_heads:
                branch_stack = []
                curr_head = head
                print("CURR HEAD", head)
                while curr_head != self.final.header:
                    block = Block.load(curr_head, kv)
                    branch_stack.append(block)
                    curr_head = block.header.parent

                ghost_head = head
                while len(branch_stack):
                    block = branch_stack.pop()
                    bh = block.header.hash()

                    # If block is already there, ignore rebuilding
                    if bh in self._index_map:
                        continue

                    key = block.get_storage_key_meta(bh)
                    data = kv.get(key)
                    meta = BlockMeta.decode(data)

                    ghost_parent = self._index_map.get(block.header.parent)
                    ghost_block = GhostBlock(block, ghost_parent)
                    ghost_block.status = meta.status
                    self._index_map[bh] = ghost_block

                if ghost_head not in self.heads:
                    self.heads.append(ghost_head)

        self.revalidate_view()

    def record_block(self, block: Block, kv: RockStore):
        parent = block.header.parent
        bh = block.header.hash()

        if bh in self._index_map:
            ghost_block = self._index_map[bh]

        else:
            if parent not in self._index_map:
                raise ValueError("Block View not setup!")

            ghost_parent = self._index_map.get(parent, None)
            if parent in self.heads:
                self.heads.remove(parent)

            self.heads.append(bh)
            ghost_block = GhostBlock(block, ghost_parent)
            self._index_map[bh] = ghost_block

        meta = ghost_block.to_meta()
        meta_key = block.get_storage_key_meta(bh)
        kv.put(meta_key, meta.encode())

        self.revalidate_view()

    def load_ghost(self, hh: HeaderHash):
        if hh not in self._index_map:
            return None

        return self._index_map[hh]

    def load_block_w_ts(self, ts: TimeSlot, kv: RockStore):
        blocks = []
        for gb in self._index_map.values():
            if gb.slot == ts:
                block = Block.load(gb.header, kv)
                blocks.append(block)

        return blocks

    def mark_as_audited(self, block: Block, kv: RockStore):
        bh = block.header.hash()

        ghost_block = self._index_map.get(bh)
        ghost_block.status = BlockStatus("audited")

        meta = ghost_block.to_meta()
        meta_key = block.get_storage_key_meta(bh)
        kv.put(meta_key, meta.encode())

        self.revalidate_view()

    def finalize(self, block: Block, kv: RockStore):
        bh = block.header.hash()

        ghost_block = self._index_map[bh]
        ghost_block.status = BlockStatus("final")


        pre_final = self.final

        if pre_final.header == bh:
            return

        if ghost_block.parent is None or ghost_block.parent.header != pre_final.header:
            raise ValueError("pre-final must be direct parent of the block being finalized")

        self._index_map.pop(pre_final.header, None)

        # TODO: Handle forked chain properly
        # def _collect_subtree_nodes(root: GhostBlock):
        #     stack = [root]
        #     seen = set()
        #     while stack:
        #         node = stack.pop()
        #         if node.header in seen:
        #             continue
        #         seen.add(node.header)
        #         for c in getattr(node, "children", []):
        #             stack.append(c)
        #     return seen

        # removed_heads = set()
        for child in pre_final.children:
            if child.header != ghost_block.header:
                child.status = BlockStatus("invalid")
                # to_remove = _collect_subtree_nodes(child)
                # removed_heads.update(to_remove)

            # child.detach_from_parent()

        del pre_final

        self.final = ghost_block
        meta = ghost_block.to_meta()
        meta_key = block.get_storage_key_meta(bh)
        kv.put(meta_key, meta.encode())

        self.revalidate_view()

    def best_block(self):
        curr_head = self.final
        best = self.final

        while True:
            children = getattr(curr_head, "children", [])

            if len(children) != 1:
                break

            next_head = children[0]
            if next_head.status != BlockStatus.audited:
                break

            best = next_head
            curr_head = next_head

        return best

    def revalidate_view(self):
        best = self.best_block()
        if not self.best or self.best.header != best.header:
            self.best = best

            # publish updates of the head of the "best" chain.
            asyncio.create_task(subscribe_best_block(best.header))

    def visualize(self, *, show_status: bool = True, show_slot: bool = True, color: bool = True):
        """
        Print the entire GhostBlock tree starting from the final block.
        Handles forks, child branches, and disconnected blocks.
        """
        if not self._index_map:
            print("<empty BlockView>")
            return

        # ANSI colors
        RESET = "\033[0m" if color else ""
        COLORS = {
            BlockStatus.audited: "\033[94m",    # blue
            BlockStatus.final: "\033[96m", # cyan
            BlockStatus.unaudited: "\033[93m",  # yellow
            BlockStatus.invalid: "\033[91m",    # red
        } if color else {s: "" for s in BlockStatus}

        def fmt_block(g: GhostBlock) -> str:
            info = g.header.hex()[:8]
            extras = []
            if show_slot:
                extras.append(f"slot={g.slot}")
            if show_status:
                extras.append(g.status.value)
            s = f"{info} ({', '.join(extras)})"
            c = COLORS.get(g.status, "")
            return f"{c}{s}{RESET}"

        # find all roots (blocks without parent)
        # currently from final block only
        roots = [self.final]
        if not roots:
            print("<no roots — possibly inconsistent tree>")
            return

        def walk(node: GhostBlock, prefix: str = "", is_last: bool = True):
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{fmt_block(node)}")

            # prepare prefix for children
            next_prefix = prefix + ("    " if is_last else "│   ")
            children = getattr(node, "children", [])
            for i, child in enumerate(children):
                walk(child, next_prefix, i == len(children) - 1)

        print("BlockView Tree:")
        print("----------------")
        for r_i, root in enumerate(sorted(roots, key=lambda x: x.slot)):
            walk(root, "", r_i == len(roots) - 1)

        # Show summary
        print("\nSummary:")
        print(f"  Final:       {self.final.header.hex()[:8] if self.final else 'None'}")
        print(f"  Best:        {self.best.header.hex()[:8] if self.best else 'None'}")
        print(f"  #Heads:      {len(self.heads)} {[head.hex()[:8] for head in self.heads]}")



viewer = BlockView()