class Memory:
    def __init__(self):
        self.data = {}

    def update_memory(self, key, value):
        self.data[key] = value

    def retrieve_memory(self, key):
        return self.data.get(key, None)

    def clear_memory(self):
        self.data.clear()

# Initialize memory
memory = Memory()