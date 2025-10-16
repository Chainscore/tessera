import pytest
from math import ceil
from jam.utils.merkle.simple_merkle import Merklizer, MerkleVisualizer

@pytest.mark.skip()
def test_merklizer():
    merklizer = Merklizer()
    visualizer = MerkleVisualizer()

    print("")
    values = [i for i in range(129)]
    og = merklizer.cd_merkle_fn(values)

    root, tree = visualizer.node(merklizer.preprocess(values))

    # root = merklizer.print_nodes(values)
    print("ROOT", root, og == root)
    # visualizer.print_tree(tree)
    #

    index = 34
    page = index // 64

    size = 6
    cnt = ceil(len(values) / (2**size))
    for i in range(cnt):
        print(f"-------------------{i}--------------------")
        # trace = merklizer.trace_fn(merklizer.preprocess(values), i)
        trace = merklizer.merkle_path_fn(values, size, i)
        print("")
        print("---------PATH----------")
        for val in trace:
            print(val, end=" ")
        print("")
        print("\n---------LEAVES----------")
        leaves = merklizer.leaf_page_fn(values, size, i)
        for val in leaves:
            print(val, end=" ")
        print("")
        if i == page:
            print("----------PROOF-GENERATED-------")
            proof = []
            sub_trace = merklizer.merkle_path_fn(leaves, 0, (index % (2**size)))
            for val in trace:
                proof.append(val)
                print(val, end=" ")
            for val in sub_trace:
                proof.append(val)
                print(val, end=" ")
            print("")
            sub_leaf = merklizer.leaf_page_fn(leaves, 0, (index % (2**size)))
            for val in sub_leaf:
                print(val, end=" ")
            print("")
            constructed_root = merklizer.reconstruct_root(
                proof, index, sub_leaf[0], len(values), 0
            )
            print(constructed_root, constructed_root == root)
            print("----------PROOF-EXPECTED-------")
            sub_trace = merklizer.merkle_path_fn(values, 0, index)
            for val in sub_trace:
                print(val, end=" ")
            print("")
            sub_leaf = merklizer.leaf_page_fn(values, 0, index)
            for val in sub_leaf:
                print(val, end=" ")
            print("")
        print("\n----------------------------------------")
