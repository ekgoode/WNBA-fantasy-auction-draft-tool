from auction_draft_environment import AuctionDraftEnv
from draft_advisor import DraftAdvisor
import random

players = [(f"Player {i}", random.randint(10, 100)) for i in range(80)]
env = AuctionDraftEnv(players)
agent_id = 0
obs = env.reset()

advisor = DraftAdvisor(input_dim=42)  # same as in training

while not env.is_done():
    if env.nomination_order[env.current_nom_index] == agent_id:
        env.nominate_player()

    if env.current_player:
        action, confidence = advisor.recommend_action(env.get_state(), agent_id)
        print(
            f"Advisor says: {'Bid' if action else 'Pass'} (confidence: {confidence:.2f})"
        )

        if action == 1:
            env.place_bid(agent_id, env.current_bid + 1)

    # simulate or insert other team logic
    env.finalize_bid()
