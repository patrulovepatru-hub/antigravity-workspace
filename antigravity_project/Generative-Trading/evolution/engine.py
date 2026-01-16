from .genome import StrategyGenome, simple_parameter_mutator
from .fitness import evaluate_fitness
import random

class EvolutionEngine:
    def __init__(self, data, population_size=10, elite_size=2):
        self.data = data
        self.population = []
        self.population_size = population_size
        self.elite_size = elite_size
        self.generation = 0

    def initialize_population(self, seed_code_list):
        """
        Bootstrap population with seed strategies.
        If fewer seeds than pop_size, fill with mutated versions.
        """
        self.population = []
        for code in seed_code_list:
            self.population.append(StrategyGenome(code))
            
        # Fill the rest
        while len(self.population) < self.population_size:
            parent = random.choice(self.population[:len(seed_code_list)]) # Pick from original seeds
            child = parent.mutate(simple_parameter_mutator)
            self.population.append(child)

    def run_generation(self):
        print(f"--- Generation {self.generation} ---")
        
        # 1. Evaluate
        for genome in self.population:
            if genome.fitness is None: # Avoid re-evaluating
                evaluate_fitness(genome, self.data)

        # 2. Sort by Fitness (Descending)
        self.population.sort(key=lambda g: g.fitness if g.fitness is not None else -9999, reverse=True)
        
        best = self.population[0]
        print(f"Best: {best.fitness:.2f} (ID: {best.id})")
        
        # 3. Selection (Elitism)
        next_gen = self.population[:self.elite_size]
        
        # 4. Reproduction
        # Simple Tournament Selection + Mutation
        while len(next_gen) < self.population_size:
            # Tournament
            candidates = random.sample(self.population, 3)
            parent = max(candidates, key=lambda g: g.fitness)
            
            # Mutate
            # TODO: Integrate LLM Mutator here
            child = parent.mutate(simple_parameter_mutator)
            next_gen.append(child)
            
        self.population = next_gen
        self.generation += 1
        return best
