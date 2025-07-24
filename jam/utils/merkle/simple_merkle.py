from math import ceil, log2


class Merklizer:
    @staticmethod
    def preprocess(values: list[int]):
        new_values = []
        for val in values:
            new_values.append(val)

        length = len(values)
        padded_length = 2 ** (ceil(log2(max(1, length))))

        for i in range(padded_length - length):
            new_values.append(0)

        return new_values

    def node(self, values: list[int]) -> int:
        sz = len(values)

        if sz == 0:
            return 0

        elif sz == 1:
            return values[0]

        else:
            mid = (sz + 1) // 2

            left = values[:mid]
            right = values[mid:]

            left_node = self.node(left)
            right_node = self.node(right)

            node_val = 1 + left_node * 10 + right_node

            return node_val

    @staticmethod
    def _print_tree(label: str, level: int, is_left: bool = None):
        indent = "    " * level
        branch = "├── " if is_left else "└── " if is_left is not None else ""
        print(f"{indent}{branch}{label}")

    def print_nodes(
        self, values: list[int], level: int = 0, is_left: bool = None
    ) -> int:
        sz = len(values)

        if sz == 0:
            label = f"ZERO: {0}"
            self._print_tree(label, level, is_left)
            return 0

        elif sz == 1:
            label = f"LEAF: {values[0]}"
            self._print_tree(label, level, is_left)
            return values[0]

        else:
            mid = (sz + 1) // 2

            left = values[:mid]
            right = values[mid:]

            self._print_tree("NODE", level, is_left)
            left_node = self.print_nodes(left, level + 1, True)
            right_node = self.print_nodes(right, level + 1, False)

            node_val = 1 + left_node + right_node

            return node_val

    @staticmethod
    def pi(values: list[int], index: int) -> int:
        sz = len(values)
        mid = (sz + 1) // 2

        if index < mid:
            return 0
        else:
            return mid

    @staticmethod
    def pb(values: list[int], index: int, case: bool) -> list[int]:
        sz = len(values)
        mid = (sz + 1) // 2
        if (index < mid) == case:
            left = values[:mid]
            return left
        else:
            right = values[mid:]
            return right

    def pt(self, values: list[int], index: int) -> list[int]:
        return self.pb(values, index, True)

    def pf(self, values: list[int], index: int) -> list[int]:
        return self.pb(values, index, False)

    def trace_fn(self, values: list[int], index: int) -> list[int]:
        sz = len(values)

        trace = []

        if sz <= 1:
            return trace

        else:
            node = self.node(self.pf(values, index))
            trace.append(node)

            new_ind = self.pi(values, index)
            trace_nodes = self.trace_fn(self.pt(values, index), index - new_ind)
            trace.extend(trace_nodes)
            return trace

    def wb_merkle_fn(self, values: list[int]) -> int:
        if len(values) == 1:
            return values[0]

        else:
            node = self.node(values)
            return node

    def cd_merkle_fn(self, values: list[int]) -> int:
        leaves = self.preprocess(values)
        node = self.node(leaves)
        return node

    def merkle_path_fn(self, values: list[int], size: int, index: int) -> list[int]:
        if index >= len(values):
            raise IndexError("index out of range")

        val = ceil(log2(max(1, len(values))) - int(size))
        # print(val)
        sz = max(0, val)
        ind = (2**size) * index

        leaves = self.preprocess(values)
        # print("here", leaves)
        path = self.trace_fn(leaves, ind)
        # print("not here", path)
        return path[:sz]

    @staticmethod
    def leaf_page_fn(values: list[int], size: int, index: int) -> list[int]:
        if index >= len(values):
            raise IndexError("index out of range")

        page = []

        ind = (2**size) * index
        val = min(ind + 2**size, len(values))

        for i in range(ind, val):
            page.append(values[i])

        return page

    def reconstruct_root(
        self, trace: list[int], index: int, leaf: int, total_nodes: int, curr: int
    ) -> int:
        if curr == len(trace):
            return leaf

        mid = ceil(total_nodes / 2)
        sibling = trace[curr]
        curr += 1
        if index >= mid:
            node_count = int(total_nodes - mid)
            index = int(index - mid)
            child_hash = self.reconstruct_root(trace, index, leaf, node_count, curr)
            return 1 + sibling + child_hash
        else:
            node_count = int(total_nodes - mid)
            child_hash = self.reconstruct_root(trace, index, leaf, node_count, curr)
            return 1 + child_hash + sibling


from typing import Optional, List, Tuple


class TreeNode:
    def __init__(
        self,
        label: str,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
    ):
        self.label = label
        self.left = left
        self.right = right

class MerkleVisualizer:
    def _display_aux(self, node: TreeNode) -> Tuple[List[str], int, int, int]:
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


    def print_tree(self, node: TreeNode):
        lines, *_ = self._display_aux(node)
        for ln in lines:
            print(ln)


    def node(self, values: list[int]) -> (int, TreeNode):
        sz = len(values)

        if sz == 0:
            return 0, TreeNode("0")

        elif sz == 1:
            return values[0], TreeNode(str(values[0]))

        else:
            mid = (sz + 1) // 2

            left = values[:mid]
            right = values[mid:]

            left_node, left_root = self.node(left)
            right_node, right_root = self.node(right)

            node_val = 1 + left_node + right_node

            return node_val, TreeNode(str(node_val), left_root, right_root)
