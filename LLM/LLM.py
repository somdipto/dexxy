import os
from typing import Dict, Optional
import requests
from pydantic import BaseModel  # if using structured data validation

# For local NLP/LLM inference
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# For OpenAI API or similar LLM services
import openai

# For environment variables
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

from typing import Dict, Optional

## LLM/LLM.py

# Define intents and expected entities
INTENTS = {
    "create_pool": ["token1", "token2", "apy"],
    "create_token": ["token_name", "supply"],
    "join_pool": ["pool_id"],
    "query_info": ["entity_type", "entity_id"],  # e.g., pool or token info query
    "general_help": []
}

# Sample few-shot examples for prompt-driven intent recognition
FEW_SHOT_EXAMPLES = [
    {"user_input": "Create a liquidity pool with APT and USDC at 7% APY", "intent": "create_pool", "entities": {"token1": "APT", "token2": "USDC", "apy": "7"}},
    {"user_input": "Launch a new token named CryptoGold with a supply of 1000000", "intent": "create_token", "entities": {"token_name": "CryptoGold", "supply": "1000000"}},
    {"user_input": "Join pool 12345", "intent": "join_pool", "entities": {"pool_id": "12345"}},
    {"user_input": "What is the status of token CryptoGold?", "intent": "query_info", "entities": {"entity_type": "token", "entity_id": "CryptoGold"}},
    {"user_input": "Help me with DeFi basics", "intent": "general_help", "entities": {}}
]

def recognize_intent(user_text: str) -> Dict[str, Optional[Dict]]:
    # Placeholder function that simulates LLM-driven intent recognition
    # In production, replace with actual LLM call or API integration
    
    user_text_lower = user_text.lower()

    for example in FEW_SHOT_EXAMPLES:
        if example["user_input"].lower() in user_text_lower or all(
            token.lower() in user_text_lower for token in example["user_input"].split()
        ):
            return {"intent": example["intent"], "entities": example["entities"]}
    
    # Naive keyword matching fallback for demo purposes
    if "create pool" in user_text_lower or "liquidity pool" in user_text_lower:
        # Extract tokens and apy with regex or NLP (to be developed)
        return {"intent": "create_pool", "entities": extract_pool_entities(user_text)}
    if "create token" in user_text_lower or "launch token" in user_text_lower:
        return {"intent": "create_token", "entities": extract_token_entities(user_text)}
    if "join pool" in user_text_lower:
        return {"intent": "join_pool", "entities": extract_join_pool_entities(user_text)}
    if "help" in user_text_lower:
        return {"intent": "general_help", "entities": {}}
    
    return {"intent": None, "entities": {}}

# Placeholder extractors to be replaced with proper NLP/entity extraction
def extract_pool_entities(text: str) -> Dict:
    # TODO: implement entity extraction from user input
    return {"token1": "APT", "token2": "USDC", "apy": "8"}

def extract_token_entities(text: str) -> Dict:
    # TODO: implement entity extraction from user input
    return {"token_name": "CryptoGold", "supply": "1000000"}

def extract_join_pool_entities(text: str) -> Dict:
    # TODO: implement entity extraction from user input
    return {"pool_id": "12345"}

# Example integration point for conversational flow handing off intent and entities
def handle_user_message(user_text: str) -> str:
    result = recognize_intent(user_text)
    intent = result.get("intent")
    entities = result.get("entities", {})

    if intent == "create_pool":
        return f"Creating liquidity pool for {entities.get('token1')} and {entities.get('token2')} with {entities.get('apy')}% APY."
    elif intent == "create_token":
        return f"Creating token named {entities.get('token_name')} with supply {entities.get('supply')}."
    elif intent == "join_pool":
        return f"Joining pool with ID {entities.get('pool_id')}."
    elif intent == "query_info":
        return f"Querying info for {entities.get('entity_type')}: {entities.get('entity_id')}."
    elif intent == "general_help":
        return "Welcome to the Aptos Assistant DeFi Suite! How can I help you with DeFi today?"
    else:
        return "Sorry, I didn't understand that. Could you please rephrase?"

# Simple test
if __name__ == "__main__":
    test_inputs = [
        "Create a liquidity pool with APT and USDC at 7% APY",
        "Launch a new token named CryptoGold with a supply of 1000000",
        "Join pool 12345",
        "What is the status of token CryptoGold?",
        "Help me with DeFi basics"
    ]
    for text in test_inputs:
        print(f"User: {text}")
        print(f"Assistant: {handle_user_message(text)}\n")


## End of LLM/LLM.py

from typing import Dict, Optional, Tuple

# Store the required parameters needed for each intent
REQUIRED_PARAMS = {
    "create_pool": ["token1", "token2", "apy"],
    "create_token": ["token_name", "supply"]
}

# Simple dialog state to track incomplete intents and collected entities per user session
class DialogState:
    def __init__(self):
        self.current_intent = None
        self.collected_entities = {}
        self.waiting_for = None  # Which entity we are waiting for

dialog_state = DialogState()

def extract_entities(text: str) -> Dict:
    """
    Placeholder for entity extraction logic. You can integrate NLP here to parse tokens, APY, etc.
    For demo, returns empty dict.
    """
    # TODO: replace with actual NLP extraction
    return {}

def get_missing_param(intent: str, collected_entities: Dict) -> Optional[str]:
    for param in REQUIRED_PARAMS.get(intent, []):
        if param not in collected_entities or not collected_entities[param]:
            return param
    return None

def generate_parameter_prompt(param_name: str) -> str:
    prompts = {
        "token1": "Please tell me the first token symbol (e.g., APT).",
        "token2": "Please tell me the second token symbol (e.g., USDC).",
        "apy": "What APY percentage would you like to set for the pool?",
        "token_name": "What is the name of the token you want to create?",
        "supply": "What is the total supply for this token?"
    }
    return prompts.get(param_name, f"Please provide {param_name}.")

def handle_multiturn_dialog(user_input: str) -> str:
    global dialog_state

    if dialog_state.current_intent is None:
        # Start new intent recognition
        intent_info = recognize_intent(user_input)
        intent = intent_info.get("intent")
        entities = intent_info.get("entities", {})

        if intent in REQUIRED_PARAMS:
            dialog_state.current_intent = intent
            dialog_state.collected_entities = entities
            missing_param = get_missing_param(intent, entities)

            if missing_param:
                dialog_state.waiting_for = missing_param
                return generate_parameter_prompt(missing_param)
            else:
                # All parameters present, confirm action
                return confirm_intent_action(intent, entities)
        elif intent is None:
            return "Sorry, I didn't understand that. Could you please rephrase?"
        else:
            # Intents with no params or simple responses
            return handle_user_message(user_input)

    else:
        # We are waiting for a param from user
        param = dialog_state.waiting_for
        dialog_state.collected_entities[param] = user_input.strip()
        # Check if more params missing
        next_missing = get_missing_param(dialog_state.current_intent, dialog_state.collected_entities)
        if next_missing:
            dialog_state.waiting_for = next_missing
            return generate_parameter_prompt(next_missing)
        else:
            # All params collected. Confirm action.
            intent = dialog_state.current_intent
            entities = dialog_state.collected_entities
            dialog_state.current_intent = None
            dialog_state.collected_entities = {}
            dialog_state.waiting_for = None
            return confirm_intent_action(intent, entities)

def confirm_intent_action(intent: str, entities: Dict) -> str:
    if intent == "create_pool":
        return f"Creating liquidity pool for {entities['token1']} and {entities['token2']} with {entities['apy']}% APY. Confirm? (yes/no)"
    elif intent == "create_token":
        return f"Creating token named {entities['token_name']} with supply {entities['supply']}. Confirm? (yes/no)"
    else:
        return handle_user_message(f"{intent} with entities {entities}")

def process_confirmation_response(user_input: str) -> Tuple[bool, str]:
    """
    Check if user confirms an action.
    Returns tuple: (confirmed: bool, message: str)
    """
    lowered = user_input.strip().lower()
    if lowered in ["yes", "y", "confirm", "sure"]:
        return True, "Confirmed. Processing your request now..."
    elif lowered in ["no", "n", "cancel"]:
        return False, "Action cancelled. How else can I help you?"
    else:
        return None, "Please reply with 'yes' or 'no' to confirm or cancel."

# To handle confirmation after prompt
awaiting_confirmation = False

def conversation_manager(user_input: str) -> str:
    global awaiting_confirmation, dialog_state

    if awaiting_confirmation:
        confirmed, msg = process_confirmation_response(user_input)
        if confirmed is True:
            awaiting_confirmation = False
            # Here, call to backend contract deployment or further processing would happen
            return msg + " (This is where we'll integrate Web3 actions.)"
        elif confirmed is False:
            awaiting_confirmation = False
            dialog_state = DialogState()  # Reset dialog state on cancel
            return msg
        else:
            return msg  # Invalid confirmation answer

    else:
        response = handle_multiturn_dialog(user_input)
        if response.lower().startswith("creating liquidity pool") or response.lower().startswith("creating token"):
            awaiting_confirmation = True
        return response


# Example interactive loop (for local testing)
if __name__ == "__main__":
    print("Welcome to Aptos Assistant DeFi Suite chatbot!")
    while True:
        user_in = input("You: ")
        bot_resp = conversation_manager(user_in)
        print("Bot:", bot_resp)


## STEP

import re

def extract_pool_entities(text: str) -> Dict:
    tokens = re.findall(r'\b[A-Z]{2,5}\b', text)
    apy_match = re.search(r'(\d+)%', text)
    return {
        "token1": tokens[0] if len(tokens) > 0 else None,
        "token2": tokens[1] if len(tokens) > 1 else None,
        "apy": apy_match.group(1) if apy_match else None
    }

def extract_token_entities(text: str) -> Dict:
    token_name_match = re.search(r'named (\w+)', text)
    supply_match = re.search(r'supply of (\d+)', text)
    return {
        "token_name": token_name_match.group(1) if token_name_match else None,
        "supply": supply_match.group(1) if supply_match else None
    }


## END OF STEP

import openai

def recognize_intent_with_api(user_text: str) -> Dict:
    prompt = f"""
You are a helpful AI that extracts user intent and entities for DeFi actions.
User input: "{user_text}"

Respond with JSON containing:
{{
  "intent": "create_pool" | "create_token" | "join_pool" | "query_info" | "general_help",
  "entities": {{
    "token1": string, "token2": string, "apy": string, "token_name": string, "supply": string, "pool_id": string, etc
  }}
}}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0
    )
    # Parse JSON from response. Assuming LLM returns JSON string.
    import json
    try:
        parsed = json.loads(response.choices[0].message.content)
        return parsed
    except Exception as e:
        print("Error parsing LLM response:", e)
        return {"intent": None, "entities": {}}
