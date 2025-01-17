class ContextManager:
    def __init__(self):
        self.context = {}

    def update_context(self, context_key, context_value):
        self.context[context_key] = context_value

    def retrieve_context(self, context_key):
        return self.context.get(context_key, None)

    def clear_context(self):
        self.context.clear()

# Initialize context manager
context_manager = ContextManager()