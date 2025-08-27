from typing import Optional, Callable

class MerkleNode:
    val: bytes
    label: str
    left: Optional["MerkleNode"]
    right: Optional["MerkleNode"]

    FALLBACK_LENGTH: int = 4
    PAD_Y: int = 0
    PAD_X: int = 2

    def __init__(
        self,
        val: bytes,
        left: Optional["MerkleNode"] = None,
        right: Optional["MerkleNode"] = None
    ):
        self.val = val
        self.label = self.labelize(val, 4)
        self.left = left
        self.right = right

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def _display_aux(self, node: "MerkleNode") -> tuple[list[str], int, int, int]:
        # Returns: lines, width, height, middle
        if node is None:
            return [], 0, 0, 0
        if not node.left and not node.right:
            line = node.label
            width = len(line)
            return [line], width, 1, width // 2

        if not node.right:
            left_lines, lw, lh, lm = self._display_aux(node.left)
            line = node.label
            w = len(line)
            first = " " * (lm + 1) + "_" * (lw - lm - 1) + line
            second = " " * lm + "/" + " " * (lw - lm - 1 + w)
            shifted = [line + " " * w for line in left_lines]
            return [first, second] + shifted, lw + w, lh + 2, lw + w // 2

        if not node.left:
            right_lines, rw, rh, rm = self._display_aux(node.right)
            line = node.label
            w = len(line)
            first = line + "_" * rm + " " * (rw - rm)
            second = " " * (w + rm) + "\\" + " " * (rw - rm - 1)
            shifted = [" " * w + rl for rl in right_lines]
            return [first, second] + shifted, rw + w, rh + 2, w // 2

        left_lines, lw, lh, lm = self._display_aux(node.left)
        right_lines, rw, rh, rm = self._display_aux(node.right)

        line = node.label
        w = len(line)
        first = " " * (lm + 1) + "_" * (lw - lm - 1) + line + "_" * rm + " " * (rw - rm)
        second = " " * lm + "/" + " " * (lw - lm - 1 + w + rm) + "\\" + " " * (rw - rm - 1)

        if lh < rh:
            left_lines += [" " * lw] * (rh - lh)
        elif rh < lh:
            right_lines += [" " * rw] * (lh - rh)

        zipped = zip(left_lines, right_lines)
        lines = [first, second] + [l + " " * w + r for l, r in zipped]
        return lines, lw + rw + w, max(lh, rh) + 2, lw + w // 2

    def labelize(self, data: bytes | None, trim_len: int = 6):
        if not data or len(data) == 0:
            return "NULL"

        hex_str = data.hex()

        if len(hex_str) >= 2 * trim_len:
            pass
        elif len(hex_str) >= self.FALLBACK_LENGTH:
            trim_len = self.FALLBACK_LENGTH / 2
        else:
            trim_len = max(1, (len(hex_str) + 1) // 2)

        label = hex_str[:trim_len] + ".." + hex_str[-trim_len:]

        return label

    def plot(self):
        lines, *_ = self._display_aux(self)
        for ln in lines:
            print(ln)

class Hash:
    @staticmethod
    def blake(data: bytes, digest_size: Optional[int] = 32):
        from hashlib import blake2b

        return blake2b(data, digest_size=digest_size).digest()

class Merklizer:
    hasher: Callable[[bytes, Optional[int]], bytes]
    NODE_PREF = b"node"
    LEAF_PREF = b"leaf"

    def __init__(self):
        self.hasher = Hash.blake

    def node(self, values: list[bytes]) -> MerkleNode:
        sz = len(values)

        if sz == 0:
            return MerkleNode(bytes(32))

        elif sz == 1:
            return MerkleNode(values[0])

        else:
            mid = (sz + 1) // 2

            left = self.node(values[:mid])
            right = self.node(values[mid:])

            val = self.hasher(self.NODE_PREF + left.val + right.val)
            return MerkleNode(val, left, right)

    def trace(self, root: MerkleNode, index: int, total_leaves: int) -> list[bytes]:
        trace = []

        if root.is_leaf() or total_leaves <= 1:
            return trace

        mid = (total_leaves + 1) // 2

        if index < mid:
            # Go Left as our node is on right side
            if root.right:
                trace.append(root.right.val)

            sub_trace = self.trace(root.left, index, mid)
            trace.extend(sub_trace)

        else:
            # Go Right as our node is on left side
            if root.left:
                trace.append(root.left.val)

            sub_trace = self.trace(root.right, index-mid, total_leaves-mid)
            trace.extend(sub_trace)

        return trace


