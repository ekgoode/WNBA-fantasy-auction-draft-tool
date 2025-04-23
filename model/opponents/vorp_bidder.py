class VORPBidder:
    def __init__(self, team_id, value_map, replacement_level):
        self.team_id = team_id
        self.value_map = value_map  # Dict of player_name -> projected_value
        self.replacement_level = replacement_level  # Float

    def should_bid(self, current_player, current_bid, budget, roster):
        vorp = self.value_map.get(current_player[0], 0) - self.replacement_level
        return current_bid < vorp and budget >= current_bid
