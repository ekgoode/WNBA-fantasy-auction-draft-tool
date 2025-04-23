import random


class AuctionDraftEnv:
    def __init__(self, players, num_teams=10, budget=100, roster_size=8):
        self.players = players  # List of (player_name, projected_value)
        self.num_teams = num_teams
        self.budget = budget
        self.roster_size = roster_size
        self.reset()

    def reset(self):
        self.remaining_players = list(self.players)
        random.shuffle(self.remaining_players)

        self.team_rosters = [[] for _ in range(self.num_teams)]
        self.team_budgets = [self.budget] * self.num_teams
        self.nomination_order = list(range(self.num_teams))
        random.shuffle(self.nomination_order)

        self.current_nom_index = 0
        self.current_player = None
        self.current_bid = 0
        self.current_bidder = None

        self.done = False
        return self._get_observation()

    def _get_observation(self):
        return {
            "remaining_players": len(self.remaining_players),
            "team_rosters": [len(r) for r in self.team_rosters],
            "team_budgets": self.team_budgets,
            "current_player": self.current_player,
            "current_bid": self.current_bid,
            "current_bidder": self.current_bidder,
            "nomination_team": self.nomination_order[self.current_nom_index],
        }

    def _min_bid_allowed(self, team_id):
        remaining_slots = self.roster_size - len(self.team_rosters[team_id])
        return max(1, self.team_budgets[team_id] - (remaining_slots - 1))

    def nominate_player(self):
        if not self.remaining_players:
            self.done = True
            return None
        self.current_player = self.remaining_players.pop(0)
        self.current_bid = 1
        self.current_bidder = self.nomination_order[self.current_nom_index]
        return self.current_player

    def place_bid(self, team_id, bid_amount):
        if bid_amount <= self.current_bid:
            return False  # must raise
        if bid_amount > self.team_budgets[team_id]:
            return False  # can't afford
        if bid_amount > self._min_bid_allowed(team_id):
            return False  # would leave too little budget

        self.current_bid = bid_amount
        self.current_bidder = team_id
        return True

    def finalize_bid(self):
        team_id = self.current_bidder
        self.team_budgets[team_id] -= self.current_bid
        self.team_rosters[team_id].append(self.current_player)

        self.current_nom_index = (self.current_nom_index + 1) % self.num_teams
        self.current_player = None
        self.current_bid = 0
        self.current_bidder = None

        if all(len(r) >= self.roster_size for r in self.team_rosters):
            self.done = True

    def is_done(self):
        return self.done

    def get_state(self):
        return self._get_observation()
