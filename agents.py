import random
import requests
import json
import re

class BaseAgent:
    def __init__(self, name="Agent"):
        self.name = name
        self.system_prompt = "You are a poker player. Play to win."

    def get_action(self, game_state_str):
        raise NotImplementedError

class RandomAgent(BaseAgent):
    def get_action(self, game_state_str):
        # Naive random action
        actions = ['fold', 'call', 'raise']
        chosen = random.choice(actions)
        amount = 0
        if chosen == 'raise':
            amount = random.randint(20, 100) # Arbitrary
        return chosen, amount

class LLMAgent(BaseAgent):
    def __init__(self, name="LLM_Bot", model_name="local-model", api_url="http://localhost:1234/v1/chat/completions", system_prompt=None):
        super().__init__(name)
        self.model_name = model_name
        self.api_url = api_url
        self.system_prompt = system_prompt or """
        You are a professional Poker Player playing a Spin & Go tournament (3-Max No Limit Hold'em).
        You are given the current Game State.
        You must output your action in a specific format.
        
        Valid Actions:
        - FOLD
        - CALL
        - RAISE <amount>
        
        Reasoning: Briefly explain your strategy (1 sentence).
        Output Format:
        Reasoning: [Reason]
        Action: [Action]
        """

    def get_action(self, game_state_str):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Current Game State:\n{game_state_str}\n\nWhat is your move?"}
        ]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return self._parse_output(content)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return 'fold', 0 # Safe fallback

    def _parse_output(self, content):
        # Regex to find Action: ...
        match = re.search(r"Action:\s*(FOLD|CALL|RAISE)(?:\s+(\d+))?", content, re.IGNORECASE)
        if match:
            action_type = match.group(1).lower()
            amount_str = match.group(2)
            amount = int(amount_str) if amount_str else 0
            return action_type, amount
        else:
            print(f"Failed to parse LLM output: {content}")
            return 'call', 0 # Default fallback
