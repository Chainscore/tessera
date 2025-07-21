def outside_in(values: list) -> list:
    """
    Returns the outside-in sequenced list of values
    https://graypaper.fluffylabs.dev/#/68eaa1f/0ea8020ebb02?v=0.6.4
    """
    ret = []
    fwd = values
    bwd = values[::-1]
    for i in range(len(values)):
        if i % 2:
            ret.append(bwd.pop(0))
        else:
            ret.append(fwd.pop(0))

    return ret
