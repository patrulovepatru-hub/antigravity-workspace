import random

class StrategyGenome:
    def __init__(self, code, parent_id=None):
        self.code = code
        self.fitness = None
        self.stats = {} # Full backtest stats
        self.parent_id = parent_id
        self.id = id(self)

    def mutate(self, mutator_func):
        """
        Apply a mutation using the provided mutator function (e.g., an LLM call).
        Returns a NEW StrategyGenome instance.
        """
        new_code = mutator_func(self.code)
        return StrategyGenome(new_code, parent_id=self.id)

    def __repr__(self):
        return f"<Genome {self.id} Fitness={self.fitness}>"

def simple_parameter_mutator(code):
    """
    A simple heuristic mutator for testing without an LLM.
    It randomly tweaks numbers found in the code.
    This is just a placeholder for the real LLM-based mutator.
    """
    import re
    
    # Find all integers
    def replace_number(match):
        val = int(match.group())
        if random.random() < 0.3: # 30% chance to change a number
            change = random.choice([-1, 1, -5, 5])
            val += change
            return str(max(1, val)) # Ensure positive
        return str(val)
        
    new_code = re.sub(r'\b\d+\b', replace_number, code)
    return new_code
