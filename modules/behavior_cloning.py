import torch
import torch.nn as nn
import torch.optim as optim
import json
import numpy as np


class BCPolicy(nn.Module):
    def __init__(self, input_dim=10, output_dim=9):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
            nn.Tanh()
        )

    def forward(self, x):
        return self.net(x)

    def predict(self, obs: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            return self(x).squeeze().numpy()

    def save(self, path: str):
        torch.save(self.state_dict(), path)

    @classmethod
    def load(cls, path: str):
        model = cls()
        model.load_state_dict(torch.load(path))
        model.eval()
        return model


def train_behavior_cloning_model(dataset_path, model_path, epochs=5, batch_size=64):
    with open(dataset_path, "r") as f:
        data = json.load(f)

    obs = np.array([entry["observation"] for entry in data], dtype=np.float32)
    acts = np.array([entry["expert_action"] for entry in data], dtype=np.float32)

    model = BCPolicy()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    for epoch in range(epochs):
        permutation = np.random.permutation(len(obs))
        obs_shuffled = obs[permutation]
        acts_shuffled = acts[permutation]

        for i in range(0, len(obs), batch_size):
            batch_obs = torch.tensor(obs_shuffled[i:i+batch_size], dtype=torch.float32)
            batch_acts = torch.tensor(acts_shuffled[i:i+batch_size], dtype=torch.float32)

            pred = model(batch_obs)
            loss = loss_fn(pred, batch_acts)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        print(f"[BC] Epoch {epoch+1}/{epochs} - Loss: {loss.item():.4f}")

    model.save(model_path)
    print(f"[BC] Saved model to {model_path}")
