import requests

class PromptMutator:
    def __init__(self, api_url="http://localhost:1234/v1/chat/completions", model_name="local-model"):
        self.api_url = api_url
        self.model_name = model_name

    def mutate_prompt(self, parent_prompt, mutation_type="random"):
        """
        Uses an LLM to rewrite the parent prompt, introducing variations.
        """
        instruction = ""
        if mutation_type == "aggressive":
            instruction = "Rewrite this poker strategy to be significantly more aggressive and bluff-heavy."
        elif mutation_type == "conservative":
            instruction = "Rewrite this poker strategy to be tighter and more risk-averse."
        else:
            instruction = "Rewrite this poker strategy to minimize weaknesses and improve decision making. Keep it concise."

        mutation_request_prompt = f"""
        You are an Expert Poker Coach.
        Here is a player's strategy (System Prompt):
        "{parent_prompt}"
        
        {instruction}
        Output ONLY the new System Prompt. Do not add conversational filler.
        """
        
        messages = [
            {"role": "system", "content": "You are a genetic algorithm component modifying text."},
            {"role": "user", "content": mutation_request_prompt}
        ]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 1.0, # High temp for diversity
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            response.raise_for_status()
            new_prompt = response.json()['choices'][0]['message']['content']
            return new_prompt.strip()
        except Exception as e:
            print(f"Mutation Failed: {e}")
            return parent_prompt # Fallback: Clone parent
