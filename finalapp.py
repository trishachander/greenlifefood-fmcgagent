# finalapp.py
import streamlit as st
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from groq import Groq
import logging
from datetime import datetime
from pathlib import Path
from memory import Memory
from context import ContextManager
from tools.tools import tools
from tools.parser import parse_tool_response
# Configuration Loader Class
class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.configs = {}
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

    def load_all_configs(self):
        """Load all configuration files from the config directory."""
        try:
            for config_file in self.config_dir.glob("*.json"):
                config_name = config_file.stem
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.configs[config_name] = json.load(f)
                except Exception as e:
                    logging.error(f"Error loading {config_file}: {str(e)}")
                    raise ValueError(f"Failed to load config file: {config_file}")
            return self.configs
        except Exception as e:
            logging.error(f"Error in load_all_configs: {str(e)}")
            raise

    def get_config(self, config_name: str):
        """Get a specific configuration by name."""
        try:
            if config_name not in self.configs:
                config_file = self.config_dir / f"{config_name}.json"
                if not config_file.exists():
                    raise FileNotFoundError(f"Config file not found: {config_file}")
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.configs[config_name] = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in {config_file}: {str(e)}")
                    raise
            return self.configs[config_name]
        except Exception as e:
            logging.error(f"Error getting config {config_name}: {str(e)}")
            raise

# Initialize memory and context
memory = Memory()
context_manager = ContextManager()

@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    category: str
    unit_size: str
    stock: int
    min_order_quantity: int

@dataclass
class CartItem:
    product_id: str
    quantity: int
    unit_price: float
    total_price: float

@dataclass
class Cart:
    items: List[CartItem]
    total: float
    status: str

class ProductCatalog:
    def __init__(self, config_loader: ConfigLoader):
        self.products = {}
        product_data = config_loader.get_config("products")
        for category, items in product_data.items():
            for product_id, details in items.items():
                self.products[product_id] = Product(
                    id=product_id,
                    name=details["name"],
                    description=details["description"],
                    price=details["price"],
                    category=details["category"],
                    unit_size=details["unit_size"],
                    stock=details["stock"],
                    min_order_quantity=details["min_order_quantity"]
                )
    
    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(product_id)

    def get_all_products(self) -> List[Product]:
        return list(self.products.values())
    
    def get_products_by_category(self, category: str) -> List[Product]:
        return [p for p in self.products.values() if p.category.lower() == category.lower()]
    
    def search_products(self, search_term: str) -> List[Product]:
        return [p for p in self.products.values() 
                if search_term.lower() in p.name.lower() or 
                   search_term.lower() in p.description.lower()]

class CartManager:
    def __init__(self):
        self.cart = Cart(items=[], total=0.0, status="active")

    def add_item(self, product: Product, quantity: int) -> bool:
        if quantity < product.min_order_quantity:
            raise ValueError(f"Minimum order quantity is {product.min_order_quantity} packs")
        
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {product.stock} packs")
        
        # Check if item already exists in cart
        for item in self.cart.items:
            if item.product_id == product.id:
                item.quantity += quantity
                item.total_price = item.quantity * item.unit_price
                self._update_total()
                return True
        
        # Add new item
        cart_item = CartItem(
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            total_price=product.price * quantity
        )
        self.cart.items.append(cart_item)
        self._update_total()
        return True

    def remove_item(self, product_id: str) -> bool:
        self.cart.items = [item for item in self.cart.items if item.product_id != product_id]
        self._update_total()
        return True

    def _update_total(self):
        self.cart.total = sum(item.total_price for item in self.cart.items)

    def clear_cart(self):
        self.cart = Cart(items=[], total=0.0, status="active")

    def get_cart_summary(self) -> Dict:
        return {
            "items": [{"product_id": item.product_id, 
                      "quantity": item.quantity,
                      "unit_price": item.unit_price,
                      "total_price": item.total_price} for item in self.cart.items],
            "total": self.cart.total
        }

class ChatBot:
    def __init__(self, api_key: str, config_loader: ConfigLoader):
        self.client = Groq(api_key=api_key)
        self.config_loader = config_loader
        self.model_config = config_loader.get_config("model_config")
        self.system_prompts = config_loader.get_config("system_prompts")
        self.product_catalog = ProductCatalog(config_loader)
        self.cart_manager = CartManager()
        self.conversation_history = []
        
        # Initialize memory with cart state
        memory.update_memory("cart", self.cart_manager)
        context_manager.update_context("last_action", None)

    def _create_context(self) -> str:
        """Create current context for LLM"""
        # Get cart state
        cart = memory.retrieve_memory("cart")
        cart_summary = self.cart_manager.get_cart_summary() if cart else {"items": [], "total": 0}
        
        # Get available products
        products = self.product_catalog.get_all_products()
        product_info = {}
        for product in products:
            product_info[product.id] = {
                "name": product.name,
                "price": product.price,
                "unit_size": product.unit_size,
                "stock": product.stock,
                "min_order": product.min_order_quantity
            }

        return json.dumps({
            "cart": cart_summary,
            "products": product_info,
            "last_action": context_manager.retrieve_context("last_action")
        })

    def process_message(self, user_message: str) -> str:
        # Add message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        try:
            # Create context-aware prompt
            system_prompt = f"""You are GreenLife Assistant, helping customers shop for organic Indian food products.

Current Context: {self._create_context()}

Your capabilities:
1. Show available products and their details
2. Add items to cart (check minimum order quantities)
3. Remove items from cart
4. Process checkout
5. Answer questions about products

Guidelines:
- Be concise and natural in responses
- Maintain context of the conversation
- Verify stock before suggesting products
- Guide users through the ordering process
- Keep track of cart state
- Use Indian Rupee (₹) for prices

Previous conversation:
{json.dumps(self.conversation_history[-5:] if len(self.conversation_history) > 0 else [])}

Respond naturally to the user's message. Do not expose technical details or function calls in your response."""

            # Get LLM response
            completion = self.client.chat.completions.create(
                model=self.model_config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )
            
            response = completion.choices[0].message.content
            
            # Update conversation history and context
            self.conversation_history.append({"role": "assistant", "content": response})
            context_manager.update_context("last_message", user_message)
            context_manager.update_context("last_response", response)
            
            # Parse LLM response for any actions (add to cart, remove from cart, etc.)
            self._handle_actions(response)
            
            return response

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again."

    def _handle_actions(self, response: str):
        """Handle any actions indicated in the LLM response using tool calls"""
        try:
            # First ask LLM to analyze the response with system prompts
            tool_selection = self.client.chat.completions.create(
                model=self.model_config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": f"""{self.system_prompts['base_prompt']}
                        
                        Current context: {self._create_context()}
                        Product format: {self.system_prompts['product_format']}
                        Cart format: {self.system_prompts['cart_format']}
                        
                        Available tools: {json.dumps(tools, indent=2)}
                        
                        Rules for tool usage:
                        1. Use exact product names and prices from the catalog
                        2. Respect minimum order quantities
                        3. Verify stock availability before actions
                        4. Calculate totals based on unit price × quantity
                        5. Format currency as ₹ with 2 decimal places
                        
                        Return tool calls in XML format:
                        <tool>tool_name</tool><arguments>{{json args}}</arguments>"""
                    },
                    {"role": "user", "content": response}
                ],
                temperature=0,
                max_tokens=self.model_config["max_tokens"]
            )
            
            # Parse tool calls from LLM response
            tool_calls = parse_tool_response(tool_selection.choices[0].message.content)
            
            # Execute each tool call and collect results
            results = []
            for tool_call in tool_calls:
                try:
                    # Let LLM handle the tool execution with system prompts
                    execution_response = self.client.chat.completions.create(
                        model=self.model_config["model"],
                        messages=[
                            {
                                "role": "system",
                                "content": f"""{self.system_prompts['base_prompt']}
                                
                                Current context: {self._create_context()}
                                Product format: {self.system_prompts['product_format']}
                                Cart format: {self.system_prompts['cart_format']}
                                
                                Handle the execution of tool: {tool_call["tool_name"]}
                                with arguments: {json.dumps(tool_call["arguments"])}
                                
                                If this is a cart operation, ensure:
                                1. Prices match the product catalog exactly
                                2. Totals are calculated as price × quantity
                                3. Cart summary follows the cart_format template"""
                            }
                        ],
                        temperature=0
                    )
                    results.append(execution_response.choices[0].message.content)
                    
                    # Update context with action
                    context_manager.update_context("last_action", {
                        "tool": tool_call["tool_name"],
                        "arguments": tool_call["arguments"],
                        "result": results[-1]
                    })
                    
                except Exception as e:
                    error_msg = self.system_prompts["error_messages"]["general"]
                    logging.error(f"Error executing tool {tool_call['tool_name']}: {str(e)}")
                    results.append(error_msg)
            
            # Update memory with cart state
            memory.update_memory("cart", self.cart_manager)
            
            return "\n".join(results) if results else None
                
        except Exception as e:
            logging.error(f"Error in tool calling: {str(e)}")
            return self.system_prompts["error_messages"]["general"]


def main():
    st.set_page_config(
        page_title="GreenLife Foods Assistant",
        page_icon="🌱",
        layout="wide"
    )
    
    config_loader = ConfigLoader()
    config_loader.load_all_configs()
    ui_config = config_loader.get_config("ui_config")

    # Apply styling
    st.markdown(f"""
    <style>
    .stTextInput > div > div > input {{
        background-color: {ui_config["colors"]["background"]};
        border-color: {ui_config["colors"]["secondary"]};
    }}
    .stButton > button {{
        background-color: {ui_config["colors"]["primary"]};
        color: white;
        border-radius: {ui_config["spacing"]["border_radius"]};
    }}
    .chat-message {{
        padding: {ui_config["spacing"]["chat_padding"]};
        border-radius: {ui_config["spacing"]["border_radius"]};
        margin-bottom: {ui_config["spacing"]["message_margin"]};
        background-color: {ui_config["colors"]["background"]};
    }}
    * {{
        font-family: {ui_config["fonts"]["primary"]}, sans-serif;
    }}
    .main {{
        padding: 2rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.title("🌱 GreenLife Foods Assistant")

    # Initialize session state
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatBot(st.secrets["GROQ_API_KEY"], config_loader)
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = st.session_state.chatbot.process_message(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()
