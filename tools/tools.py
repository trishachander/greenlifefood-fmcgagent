# tools/tools.py
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_product_info",
            "description": "Get formatted list of products, by category if specified",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category (grains/spices/pulses)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of product to add"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of packs to add"
                    }
                },
                "required": ["product_name", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart_summary",
            "description": "Get current cart contents and total",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove a product from cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of product to remove"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkout",
            "description": "Process checkout for current cart",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]