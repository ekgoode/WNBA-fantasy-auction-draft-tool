class NaiveBidder:
    def __init__(self, team_id, value_map):
        self.team_id = team_id
        self.value_map = value_map  # Dict of player_name -> projected_value

    def should_bid(self, current_player, current_bid, budget, roster):
        projected_value = self.value_map.get(current_player[0], 0)
        return current_bid < projected_value and budget >= current_bid
