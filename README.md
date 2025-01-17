# GreenLife Foods Chatbot Agent

## Project Overview
This project implements an AI chatbot agent to streamline the order capture process for **GreenLife Foods**, a medium-sized FMCG company specializing in organic food products. The chatbot interacts with distributors and retailers, providing them with product information, managing their shopping cart, and facilitating the ordering process.

---

## Prerequisites
- **Python**: 3.7 or higher
- **Streamlit**: For the web interface
- **Groq API**: For LLM interactions
- **Python Packages**: Listed in `requirements.txt`

---

## Installation

### Clone the Repository
```bash
git clone https://github.com/yourusername/greenlife-chatbot.git
cd greenlife-chatbot
```

## Install dependencies
```
pip install -r requirements.txt
```
## Usage
### Start the Streamlit App
```
streamlit run finalapp.py
```
### Access the Chatbot
1. Open your web browser.
2. Navigate to http://localhost:8501/.
3. Interact with the chatbot to explore products, manage your cart, and place orders.

## Secrets Configuration

- Copy `secrets.example.toml` to `secrets.toml`.
- Replace placeholder values with your actual API keys.