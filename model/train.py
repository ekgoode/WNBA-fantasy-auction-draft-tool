import random
from opponents.naive_bidder import NaiveBidder
from opponents.star_bidder import StarBidder
from opponents.vorp_bidder import VORPBidder
from agent.agent_model import PolicyNetwork
from auction_draft_environment import AuctionDraftEnv
import torch
import os


def create_opponents(value_map, replacement_level, star_threshold, agent_id):
    bots = []
    for team_id in range(10):
        if team_id == agent_id:
            bots.append(None)  # this is the RL agent
            continue
        if team_id % 3 == 0:
            bots.append(NaiveBidder(team_id, value_map))
        elif team_id % 3 == 1:
            bots.append(VORPBidder(team_id, value_map, replacement_level))
        else:
            bots.append(StarBidder(team_id, value_map, star_threshold))
    return bots


def encode_state(obs, agent_id):
    state = []

    # Normalize budgets and roster sizes
    state += [b / 100 for b in obs["team_budgets"]]
    state += [r / 8 for r in obs["team_rosters"]]

    # Current player projected value
    state.append(obs["current_player"][1] / 100 if obs["current_player"] else 0)

    # Normalize current bid
    state.append(obs["current_bid"] / 100)

    # One-hot for current bidder
    one_hot_bidder = [0] * 10
    if obs["current_bidder"] is not None:
        one_hot_bidder[obs["current_bidder"]] = 1
    state += one_hot_bidder

    # One-hot for nomination team
    one_hot_nom = [0] * 10
    one_hot_nom[obs["nomination_team"]] = 1
    state += one_hot_nom

    return torch.tensor(state, dtype=torch.float32)


def reinforce_train(env, policy_net, agent_id, optimizer, opponents, n_episodes=1000):
    for episode in range(n_episodes):
        log_probs = []
        rewards = []
        obs = env.reset()

        while not env.is_done():
            if env.nomination_order[env.current_nom_index] != agent_id:
                env.nominate_player()

            if env.current_player is not None:
                # RL agent's turn
                state_tensor = encode_state(env.get_state(), agent_id)
                action_probs = policy_net(state_tensor)
                dist = torch.distributions.Categorical(action_probs)
                action = dist.sample()

                if action.item() == 1:
                    bid = env.current_bid + 1
                    legal = env.place_bid(agent_id, bid)
                    if legal:
                        log_probs.append(dist.log_prob(action))
                else:
                    log_probs.append(dist.log_prob(action))

                # Opponent turns
                for team_id in range(env.num_teams):
                    if team_id == agent_id:
                        continue
                    bot = opponents[team_id]
                    if bot and env.current_player:
                        if bot.should_bid(
                            env.current_player,
                            env.current_bid,
                            env.team_budgets[team_id],
                            env.team_rosters[team_id],
                        ):
                            env.place_bid(team_id, env.current_bid + 1)

            # Simulate finalization when all others pass (simplified)
            if random.random() < 0.3:
                env.finalize_bid()

        # Final reward: value of team
        reward = sum(p[1] for p in env.team_rosters[agent_id])
        loss = -torch.stack(log_probs).sum() * reward

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if episode % 50 == 0:
            print(f"Episode {episode}, Reward: {reward}")


if __name__ == "__main__":
    players = [(f"Player {i}", random.randint(10, 100)) for i in range(80)]
    value_map = {p[0]: p[1] for p in players}
    replacement_level = 20
    star_threshold = 80
    agent_id = 0

    env = AuctionDraftEnv(players)
    opponents = create_opponents(value_map, replacement_level, star_threshold, agent_id)
    input_dim = 10 * 2 + 1 + 1 + 10 + 10  # matches your encode_state
    policy_net = PolicyNetwork(input_dim)
    optimizer = torch.optim.Adam(policy_net.parameters(), lr=0.01)

    reinforce_train(env, policy_net, agent_id, optimizer, n_episodes=500)

    os.makedirs("saved_models", exist_ok=True)
    torch.save(policy_net.state_dict(), "saved_models/policy_net.pt")
