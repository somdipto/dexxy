import re
from typing import Dict, Optional, Tuple

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

REQUIRED_PARAMS = {
    "create_pool": ["token1", "token2", "apy"],
    "create_token": ["token_name", "supply"]
}

# Dialog State to handle multi-turn conversations
class DialogState:
    def __init__(self):
        self.current_intent = None
        self.collected_entities = {}
        self.waiting_for = None  # entity name we expect next

dialog_state = DialogState()
awaiting_confirmation = False

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

def extract_join_pool_entities(text: str) -> Dict:
    pool_id_match = re.search(r'pool (\d+)', text)
    return {
        "pool_id": pool_id_match.group(1) if pool_id_match else None
    }

import os
import openai
import json
from dotenv import load_dotenv

# Load environment variables from .env

load_dotenv()  # loads .env file variables
print(os.environ.get("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY missing. Please add it to .env or environment variables")



import json
from openai import OpenAI
from openai import OpenAIError
client = OpenAI(api_key=api_key)
# Initialize the client once (put this near your main setup code)
client = OpenAI()

def recognize_intent(user_text: str) -> dict:
    """
    Calls OpenAI GPT to extract intent and entities from user input.
    """
    prompt = f"""
You are a helpful AI assistant specialized in understanding DeFi user intents and extracting entities.
User input: \"{user_text}\"
Reply ONLY with a JSON object with fields:
{{
  "intent": one of ["create_pool", "create_token", "join_pool", "query_info", "general_help", null],
  "entities": {{
    "token1": string or null,
    "token2": string or null,
    "apy": string or null,
    "token_name": string or null,
    "supply": string or null,
    "pool_id": string or null,
    "entity_type": string or null,
    "entity_id": string or null
  }}
}}
Ensure valid JSON without extra text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        json_str = response.choices[0].message.content.strip()
        parsed = json.loads(json_str)
        return parsed
    except (json.JSONDecodeError, KeyError, OpenAIError) as e:
        print("OpenAI API or JSON Parsing error:", e)
        # Fallback to empty/no intent
        return {"intent": None, "entities": {}}

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

def confirm_intent_action(intent: str, entities: Dict) -> str:
    if intent == "create_pool":
        return f"Creating liquidity pool for {entities['token1']} and {entities['token2']} with {entities['apy']}% APY. Confirm? (yes/no)"
    elif intent == "create_token":
        return f"Creating token named {entities['token_name']} with supply {entities['supply']}. Confirm? (yes/no)"
    elif intent == "join_pool":
        return f"Joining pool with ID {entities.get('pool_id')}. Confirm? (yes/no)"
    elif intent == "query_info":
        return f"Querying info for {entities.get('entity_type')}: {entities.get('entity_id')}."
    elif intent == "general_help":
        return "Welcome to the Aptos Assistant DeFi Suite! How can I help you with DeFi today?"
    else:
        return "Sorry, I couldn't process your request."

def process_confirmation_response(user_input: str) -> Tuple[Optional[bool], str]:
    lowered = user_input.strip().lower()
    if lowered in ["yes", "y", "confirm", "sure"]:
        return True, "Confirmed. Processing your request now..."
    elif lowered in ["no", "n", "cancel"]:
        return False, "Action cancelled. How else can I help you?"
    else:
        return None, "Please reply with 'yes' or 'no' to confirm or cancel."

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
            return confirm_intent_action(intent, entities)

    else:
        # We are waiting for a param from user
        param = dialog_state.waiting_for
        dialog_state.collected_entities[param] = user_input.strip()
        next_missing = get_missing_param(dialog_state.current_intent, dialog_state.collected_entities)
        if next_missing:
            dialog_state.waiting_for = next_missing
            return generate_parameter_prompt(next_missing)
        else:
            intent = dialog_state.current_intent
            entities = dialog_state.collected_entities
            dialog_state.current_intent = None
            dialog_state.collected_entities = {}
            dialog_state.waiting_for = None
            return confirm_intent_action(intent, entities)

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

def conversation_manager(user_input: str) -> str:
    global awaiting_confirmation, dialog_state

    if awaiting_confirmation:
        confirmed, msg = process_confirmation_response(user_input)
        if confirmed is True:
            awaiting_confirmation = False
            # Placeholder for backend integration (e.g., contract deployment)
            return msg + " (This is where we'll integrate Web3 actions.)"
        elif confirmed is False:
            awaiting_confirmation = False
            dialog_state = DialogState()  # Reset dialog state on cancel
            return msg
        else:
            return msg
    else:
        response = handle_multiturn_dialog(user_input)
        if response.lower().startswith("creating liquidity pool") or response.lower().startswith("creating token") or response.lower().startswith("joining pool"):
            awaiting_confirmation = True
        return response

# Example interactive loop (local testing)
if __name__ == "__main__":
    print("Welcome to Aptos Assistant DeFi Suite chatbot!")
    while True:
        user_in = input("You: ")
        bot_resp = conversation_manager(user_in)
        print("Bot:", bot_resp)
