class StarBidder:
    def __init__(self, team_id, value_map, star_threshold):
        self.team_id = team_id
        self.value_map = value_map  # Dict of player_name -> projected_value
        self.star_threshold = star_threshold  # Float

    def should_bid(self, current_player, current_bid, budget, roster):
        player_value = self.value_map.get(current_player[0], 0)
        if player_value >= self.star_threshold:
            return current_bid < (player_value * 1.2) and budget >= current_bid
        return False