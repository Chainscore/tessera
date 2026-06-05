import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

from jam.api.rpc.subscription_handlers import subscribe_best_block, subscriptions_enabled
from jam.block import Block
from jam.models.protocol.core import TimeSlot
from jam.models.protocol.crypto import OpaqueHash, HeaderHash, StateRoot

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


@dataclass
class HeaderMeta:
    slot: TimeSlot
    parent: HeaderHash
    parent_state_root: StateRoot


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

    def __init__ (self, block: Optional[Block] = None, parent: Optional["GhostBlock"] = None):
        self.status = BlockStatus("unaudited")
        if block is None:
            self.header = HeaderHash(32)
            self.slot = TimeSlot(0)
            self.children = TypedVector[GhostBlock]([])
            self.parent = parent
            self.status = BlockStatus("final")
            return

        self.header = block.header.hash()
        self.slot = block.header.slot
        self.children = TypedVector[GhostBlock]([])
        self.parent = parent

        if parent is not None:
            parent.children.append(self)
            # if len(parent.children) > 1:
            #     print("FORK DETECTED AT BLOCK", parent.header.hex())

    def detach_from_parent(self):
        if self.parent:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
            self.parent = None

class BlockView:
    final: GhostBlock
    heads: Heads
    best: Optional[GhostBlock]

    _index_map: Dict[HeaderHash, GhostBlock]
    _ancestor_meta: Dict[HeaderHash, HeaderMeta]

    def __init__(self):
        self.final = GhostBlock()
        self.heads = Heads([])
        self.acceptable = []
        self.best = None

        # map Header Hash -> GhostBlock for quick lookup
        self._index_map = dict[HeaderHash, GhostBlock]({})
        self._ancestor_meta = dict[HeaderHash, HeaderMeta]({})

        # Highest slot whose finalized history has already been pruned.
        self._pruned_upto_slot = 0

    def initialize(self, kv: RockStore):
        self._index_map = {}
        self._ancestor_meta = {}
        self._pruned_upto_slot = 0
        from jam.finality.finality import Finality

        if not kv.get(Finality.FINAL_KEY):
            self.final = GhostBlock()
            self.heads = Heads([self.final.header])
            self.best = self.final
            self._index_map[self.final.header] = self.final
            return

        latest_heads = Finality.load_heads(kv)
        final_block = Finality.load_final(kv)

        ghost_final = GhostBlock(final_block)
        self.final = ghost_final
        final_hash = final_block.header.hash()
        self._index_map[final_hash] = ghost_final
        self._record_header_meta(final_hash, final_block.header)
        self._load_finalized_ancestor_meta(final_block.header, kv)
        ghost_final.status = BlockStatus("final")

        if (isinstance(latest_heads, Block) or
                (len(latest_heads) == 1 and latest_heads[0] == ghost_final.header)
        ):
            self.heads = Heads([ghost_final.header])

        else:
            for head in latest_heads:
                branch_stack = []
                curr_head = head
                while curr_head != self.final.header:
                    block = Block.load(curr_head, kv)
                    self._record_header_meta(curr_head, block.header)
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
                    self._record_header_meta(bh, block.header)

                if ghost_head not in self.heads:
                    self.heads.append(ghost_head)

        self.revalidate_view()

    def _record_header_meta(self, header_hash: HeaderHash, header):
        self._ancestor_meta[HeaderHash(header_hash)] = HeaderMeta(
            slot=header.slot,
            parent=header.parent,
            parent_state_root=header.parent_state_root,
        )

    def _load_header_meta(self, header_hash: HeaderHash, kv: RockStore | None):
        meta = self._ancestor_meta.get(header_hash)
        if meta is not None or kv is None:
            return meta

        header = Block.load_header(header_hash, kv)
        if header is None:
            return None

        self._record_header_meta(header_hash, header)
        return self._ancestor_meta[header_hash]

    def _load_finalized_ancestor_meta(self, header, kv: RockStore):
        from jam.utils.constants import LOOKUP_ANCHOR_MAX_AGE

        min_slot = int(header.slot) - LOOKUP_ANCHOR_MAX_AGE
        parent_hash = header.parent

        while parent_hash != HeaderHash(32):
            parent_header = Block.load_header(parent_hash, kv)
            if parent_header is None:
                return

            self._record_header_meta(parent_hash, parent_header)
            if int(parent_header.slot) < min_slot:
                return

            parent_hash = parent_header.parent

    def _prune_ancestor_meta(self):
        from jam.utils.constants import LOOKUP_ANCHOR_MAX_AGE

        min_slot = int(self.final.slot) - LOOKUP_ANCHOR_MAX_AGE
        for header_hash, meta in list(self._ancestor_meta.items()):
            if header_hash in self._index_map:
                continue
            if int(meta.slot) < min_slot:
                self._ancestor_meta.pop(header_hash, None)

    def lookup_anchor_context_valid(self, head_header, context, kv: RockStore | None = None) -> bool:
        from jam.utils.constants import LOOKUP_ANCHOR_MAX_AGE

        min_slot = int(head_header.slot) - LOOKUP_ANCHOR_MAX_AGE
        child_meta = HeaderMeta(
            slot=head_header.slot,
            parent=head_header.parent,
            parent_state_root=head_header.parent_state_root,
        )
        seen = set()

        while child_meta.parent != HeaderHash(32) and child_meta.parent not in seen:
            parent_hash = child_meta.parent
            seen.add(parent_hash)
            parent_meta = self._load_header_meta(parent_hash, kv)
            if parent_meta is None:
                return False

            if int(parent_meta.slot) < min_slot:
                return False

            if parent_hash == context.lookup_anchor:
                return (
                    parent_meta.slot == context.lookup_anchor_slot
                    and child_meta.parent_state_root == context.lookup_anchor_state_root
                )

            child_meta = parent_meta

        return False

    def record_block(self, block: Block, kv: RockStore):
        parent = block.header.parent
        bh = block.header.hash()
        self._record_header_meta(bh, block.header)

        if bh in self._index_map:
            ghost_block = self._index_map[bh]

        else:
            # if parent not in self._index_map:
            #     # print("Block View not setup!")
            #     raise ValueError("Block View not setup!")

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
        self._prune_ancestor_meta()

    def _delete_block_keys(self, ghost: "GhostBlock", kv: RockStore):
        from jam.state.storage import StateStorage

        hh = ghost.header
        for key in (
            Block.get_storage_key_block(hh),
            Block.get_storage_key_meta(hh),
            StateStorage.get_storage_key(hh),
        ):
            try:
                kv.delete(key)
            except Exception:
                pass

    def prune_history(self, kv: RockStore):
        """Delete finalized blocks, metadata and per-block state diffs older than
        the retention window behind the finalized slot when explicitly enabled."""
        from jam.state.storage import StateStorage
        from jam.utils.constants import PRUNE_BLOCK_HISTORY, STATE_HISTORY_RETENTION

        if not PRUNE_BLOCK_HISTORY:
            return

        threshold = int(self.final.slot) - STATE_HISTORY_RETENTION
        if threshold <= self._pruned_upto_slot:
            return

        from_slot = self._pruned_upto_slot + 1
        pruned_blocks = 0
        for slot in range(from_slot, threshold + 1):
            slot_key = Block.get_storage_key_slot(TimeSlot(slot))
            hh = kv.get(slot_key)
            if hh:
                for key in (
                    Block.get_storage_key_block(hh),
                    Block.get_storage_key_meta(hh),
                    StateStorage.get_storage_key(hh),
                ):
                    try:
                        kv.delete(key)
                    except Exception:
                        pass
                try:
                    kv.delete(slot_key)
                except Exception:
                    pass
                pruned_blocks += 1

        self._pruned_upto_slot = threshold
        print(
            f"[prune] finalized={int(self.final.slot)} "
            f"slots={from_slot}..{threshold} pruned_blocks={pruned_blocks} "
            f"retention={STATE_HISTORY_RETENTION} pruned_upto={self._pruned_upto_slot}",
            flush=True,
        )

    def _detach_subtree(self, ghost: "GhostBlock", kv: RockStore):
        stack = [ghost]
        while stack:
            node = stack.pop()
            for child in list(getattr(node, "children", [])):
                stack.append(child)
            self._index_map.pop(node.header, None)
            self._ancestor_meta.pop(node.header, None)
            if node.header in self.heads:
                self.heads.remove(node.header)
            self._delete_block_keys(node, kv)

    def discard(self, block: Block, kv: RockStore):
        bh = block.header.hash()
        ghost = self._index_map.get(bh)
        if ghost is None:
            return

        parent = ghost.parent
        if parent is not None:
            try:
                parent.children.remove(ghost)
            except ValueError:
                pass

        self._detach_subtree(ghost, kv)

        if parent is not None and not getattr(parent, "children", []):
            if parent.header in self._index_map and parent.header not in self.heads:
                self.heads.append(parent.header)

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
            print("WARN: pre-final must be direct parent of the block being finalized")
            # raise ValueError("pre-final must be direct parent of the block being finalized")

        self._index_map.pop(pre_final.header, None)
        if pre_final.header in self.heads:
            self.heads.remove(pre_final.header)

        for child in list(pre_final.children):
            if child.header != ghost_block.header:
                self._detach_subtree(child, kv)

        ghost_block.detach_from_parent()
        del pre_final

        self.final = ghost_block
        meta = ghost_block.to_meta()
        meta_key = block.get_storage_key_meta(bh)
        kv.put(meta_key, meta.encode())

        self.revalidate_view()
        self._prune_ancestor_meta()
        self.prune_history(kv)

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
            if subscriptions_enabled():
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
