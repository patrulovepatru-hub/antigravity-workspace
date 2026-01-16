import random
from treys import Deck, Evaluator, Card

class PokerEnv:
    def __init__(self, num_players=3, starting_stack=500, small_blind=10, ante=0):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.ante = ante
        
        self.evaluator = Evaluator()
        self.reset_tournament()

    def reset_tournament(self):
        self.players = [{'id': i, 'stack': self.starting_stack, 'active': True, 'name': f'Player_{i}'} for i in range(self.num_players)]
        self.blind_level = 0
        self.dealer_pos = 0
        self.reset_hand()

    def reset_hand(self):
        # Check if tournament is over
        active_players = [p for p in self.players if p['stack'] > 0]
        if len(active_players) <= 1:
            return None # Tournament over

        # Initialize pot and community cards
        self.pot = 0
        self.community_cards = []
        self.current_bet = 0
        
        # Secure Randomness for "Legit" Generator
        import secrets
        self.rng = secrets.SystemRandom()
        
        # Reset player states for the hand
        for p in self.players:
            p['hand'] = []
            p['current_bet'] = 0
            p['folded'] = False
            p['all_in'] = False
            if p['stack'] == 0:
                p['active'] = False
            else:
                p['active'] = True

        # Deal hands with secure shuffle
        self.deck = Deck()
        self.deck.shuffle = lambda: self.rng.shuffle(self.deck.cards) # Monkey patch shuffle
        self.deck.shuffle()
        
        for p in self.players:
            if p['active']:
                p['hand'] = self.deck.draw(2)

        # Blinds
        # Simple button movement: Dealer moves 1 spot each hand
        sb_pos = (self.dealer_pos + 1) % self.num_players
        bb_pos = (self.dealer_pos + 2) % self.num_players
        
        # Ensure only active players pay blinds (simplified for 3-max, robust logic needs to skip inactive)
        # For Spin & Go, usually players are removed when bust, so we just iterate active players
        active_indices = [i for i, p in enumerate(self.players) if p['active']]
        
        # Rotational logic for active players
        # Find index of dealer in active_indices
        try:
            dealer_active_idx = active_indices.index(self.dealer_pos)
        except ValueError:
            dealer_active_idx = 0 # Fallback
            
        sb_active_idx = (dealer_active_idx + 1) % len(active_indices)
        bb_active_idx = (dealer_active_idx + 2) % len(active_indices)
        
        self.sb_pos = active_indices[sb_active_idx]
        self.bb_pos = active_indices[bb_active_idx]
        
        # Post Blinds
        self._post_bet(self.sb_pos, self.small_blind)
        self._post_bet(self.bb_pos, self.big_blind)
        
        self.current_bet = self.big_blind
        
        # Action starts after BB
        self.current_player_idx = (bb_active_idx + 1) % len(active_indices)
        self.active_iter_idx = self.current_player_idx # Index in active_indices list
        
        self.stage = 'PREFLOP' 
        self.aggressor_idx = None # Track who made the last raise for round ending logic

        return self._get_state_str()

    def _post_bet(self, player_idx, amount):
        player = self.players[player_idx]
        actual_bet = min(player['stack'], amount)
        player['stack'] -= actual_bet
        player['current_bet'] += actual_bet
        self.pot += actual_bet
        if player['stack'] == 0:
            player['all_in'] = True
        return actual_bet

    def step(self, action_type, amount=0):
        """
        action_type: 'fold', 'call', 'raise'
        amount: raise amount (total bet amount, not increment)
        """
        active_indices = [i for i, p in enumerate(self.players) if p['active']]
        if not active_indices:
            return "GAME_OVER", 0
            
        current_p_idx = active_indices[self.active_iter_idx]
        player = self.players[current_p_idx]
        
        if action_type == 'fold':
            player['folded'] = True
            player['active'] = False # Temporarily remove from hand
        
        elif action_type == 'call':
            to_call = self.current_bet - player['current_bet']
            self._post_bet(current_p_idx, to_call)
            
        elif action_type == 'raise':
            # Min raise check could serve here
            raise_amount = max(amount, self.current_bet * 2) # Simplified min raise
            to_add = raise_amount - player['current_bet']
            self._post_bet(current_p_idx, to_add)
            self.current_bet = player['current_bet']
            self.aggressor_idx = self.active_iter_idx # Reset round completion

        # Move to next player
        # Check if round is over
        # Round is over if all active players have matched the current bet OR are all-in
        # AND everyone has acted at least once (unless big blind check)
        
        # Simplified next player logic
        next_iter_idx = (self.active_iter_idx + 1) % len(active_indices)
        
        # Determine if we should deal next cards or just move to next player
        # If one player left -> Winner
        active_in_hand = [p for p in self.players if p['active'] and not p['folded']]
        if len(active_in_hand) == 1:
            self._distribute_pot(active_in_hand[0])
            self.dealer_pos = (self.dealer_pos + 1) % self.num_players
            return "HAND_OVER", self.reset_hand()

        # Check for round completion
        # If all players matching current bet (or allin)
        all_matched = True
        for p in active_in_hand:
            if not p['all_in'] and p['current_bet'] != self.current_bet:
                all_matched = False
                break
        
        if all_matched and (self.aggressor_idx is not None or self.stage != 'PREFLOP' or action_type != 'raise'): 
            # Preflop special case for BB option is tricky, simplifying for MVP
            self._next_street()
            self.active_iter_idx = self._find_first_actor_after_button()
        else:
            self.active_iter_idx = next_iter_idx

        return "playing", self._get_state_str()

    def _find_first_actor_after_button(self):
        # find the first active non-folded player after dealer
        active_indices = [i for i, p in enumerate(self.players) if p['active']]
        # Just simple rotation for MVP
        return 0 

    def _next_street(self):
        for p in self.players:
            p['current_bet'] = 0
        self.current_bet = 0
        self.aggressor_idx = None
        
        if self.stage == 'PREFLOP':
            self.stage = 'FLOP'
            self.community_cards = self.deck.draw(3)
        elif self.stage == 'FLOP':
            self.stage = 'TURN'
            self.community_cards.append(self.deck.draw(1))
        elif self.stage == 'TURN':
            self.stage = 'RIVER'
            self.community_cards.append(self.deck.draw(1))
        elif self.stage == 'RIVER':
            self._showdown()
            
    def _showdown(self):
        active_in_hand = [p for p in self.players if not p['folded'] and p['active']]
        scores = []
        for p in active_in_hand:
            score = self.evaluator.evaluate(self.community_cards, p['hand'])
            scores.append((score, p))
        
        # Lower score is better in treys
        scores.sort(key=lambda x: x[0])
        best_player = scores[0][1]
        
        # Handle ties later (pot split), MVP winner take all
        self._distribute_pot(best_player)
        self.dealer_pos = (self.dealer_pos + 1) % self.num_players
    
    def _distribute_pot(self, winner):
        winner['stack'] += self.pot
        self.pot = 0
        
    def _get_state_str(self):
        # Create a text representation for the LLM
        active_indices = [i for i, p in enumerate(self.players) if p['active']]
        current_p = self.players[active_indices[self.active_iter_idx]]
        
        comm_str = [Card.int_to_str(c) for c in self.community_cards]
        hand_str = [Card.int_to_str(c) for c in current_p['hand']]
        
        return f"""
        Stage: {self.stage}
        Pot: {self.pot}
        Your Stack: {current_p['stack']}
        To Call: {self.current_bet - current_p['current_bet']}
        Community Cards: {comm_str}
        Your Hand: {hand_str}
        """

