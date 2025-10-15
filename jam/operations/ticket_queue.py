class Queue:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            return None
        return self.items.pop(0)

    def is_empty(self):
        return self.items == []

    def length(self):
        return len(self.items)

global ticket_queue

def setup_ticket_queue():
    new_ticket_queue = Queue()
    global ticket_queue
    ticket_queue = new_ticket_queue