import torch
from agent.agent_model import PolicyNetwork
from train import encode_state  # or move it to a shared module


class DraftAdvisor:
    def __init__(self, input_dim, model_path="saved_models/policy_net.pt"):
        self.policy = PolicyNetwork(input_dim)
        self.policy.load_state_dict(torch.load(model_path))
        self.policy.eval()

    def recommend_action(self, obs, agent_id):
        state_tensor = encode_state(obs, agent_id)
        with torch.no_grad():
            action_probs = self.policy(state_tensor)
        action = torch.argmax(action_probs).item()  # 1 = bid, 0 = pass
        return action, action_probs[1].item()  # also return confidence in bidding
