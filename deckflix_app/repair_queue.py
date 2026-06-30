repair_queue = []


def add(item):
    if item not in repair_queue:
        repair_queue.append(item)


def clear():
    repair_queue.clear()


def items():
    return list(repair_queue)


def count():
    return len(repair_queue)
