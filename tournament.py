from poker_env import PokerEnv
from agents import LLMAgent, RandomAgent
from evolution import PromptMutator
import json
import time

class Tournament:
    def __init__(self, num_generations=5, games_per_gen=10, log_file="tournament_data.jsonl"):
        self.num_generations = num_generations
        self.games_per_gen = games_per_gen
        self.population = []
        self.mutator = PromptMutator()
        self.log_file = log_file
        
        # Clear log file
        with open(self.log_file, 'w') as f:
            pass
        
    def log_event(self, event_type, data):
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            "data": data
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def initialize_population(self, size=3):
        # Gen 0
        base_prompt = """
        You are a professional Poker Player.
        Play tight-aggressive. 
        Valid Actions: FOLD, CALL, RAISE <amount>.
        Output Format:
        Reasoning: ...
        Action: [Action]
        """
        for i in range(size):
            agent = LLMAgent(name=f"Gen0_Agent{i}", system_prompt=base_prompt)
            self.population.append(agent)
            self.log_event("agent_creation", {"name": agent.name, "prompt": base_prompt})

    def run(self):
        for gen in range(self.num_generations):
            print(f"=== Generation {gen} ===")
            self.log_event("generation_start", {"gen": gen})
            scores = {agent.name: 0 for agent in self.population}
            
            # Batch of Games
            for game_idx in range(self.games_per_gen):
                # Basic Round Robin or Free For All in 3-max
                players = self.population[:3] 
                winner_name = self.play_match(players, game_id=f"G{gen}_M{game_idx}")
                if winner_name:
                    scores[winner_name] += 1
            
            # Ranking
            sorted_agents = sorted(self.population, key=lambda x: scores[x.name], reverse=True)
            print(f"Gen {gen} Results: {scores}")
            self.log_event("generation_results", scores)
            
            if gen < self.num_generations - 1:
                self.evolve(sorted_agents, gen)
                
    def play_match(self, agents, game_id):
        env = PokerEnv(num_players=len(agents))
        env_state = env.reset_hand()
        
        hands_played = 0
        max_hands = 30
        
        match_log = []
        
        while hands_played < max_hands:
            if env_state is None: 
                break
                
            game_over = False
            while not game_over:
                active_indices = [i for i, p in enumerate(env.players) if p['active']]
                current_idx = active_indices[env.active_iter_idx]
                current_agent = agents[current_idx]
                
                # Get Action
                try:
                    action, amount = current_agent.get_action(env_state)
                except Exception as e:
                    print(f"Agent Error: {e}")
                    action, amount = 'fold', 0
                
                # Log the decision context
                decision_record = {
                    "game_id": game_id,
                    "hand_num": hands_played,
                    "agent": current_agent.name,
                    "state_view": env_state,
                    "action": action,
                    "amount": amount
                }
                self.log_event("move", decision_record)
                print(f"{current_agent.name}: {action} {amount}")
                
                # Step Env
                status, state_or_res = env.step(action, amount)
                
                if status == "HAND_OVER":
                    print("Hand Over")
                    hands_played += 1
                    game_over = True
                    env_state = state_or_res
                elif status == "GAME_OVER":
                     return None
                else:
                    env_state = state_or_res 
                    
        # Winner
        final_stacks = [p['stack'] for p in env.players]
        best_idx = final_stacks.index(max(final_stacks))
        winner = agents[best_idx].name
        
        self.log_event("match_end", {"game_id": game_id, "winner": winner, "stacks": final_stacks})
        return winner

    def evolve(self, sorted_agents, gen):
        best_agent = sorted_agents[0]
        self.log_event("evolution_source", {"parent": best_agent.name, "prompt": best_agent.system_prompt})
        
        new_population = [best_agent]
        
        # Mutate
        for i in range(2):
            new_prompt = self.mutator.mutate_prompt(best_agent.system_prompt)
            new_agent = LLMAgent(name=f"Gen{gen+1}_Mutant_{i}", system_prompt=new_prompt)
            new_population.append(new_agent)
            self.log_event("agent_creation", {"name": new_agent.name, "parent": best_agent.name, "prompt": new_prompt})
            
        self.population = new_population

if __name__ == "__main__":
    # Increased games per gen for better data
    t = Tournament(num_generations=3, games_per_gen=5) 
    t.initialize_population()
    t.run()
