"""
aae_adaptive_ae_demo.py
=========================
No pretrained checkpoints exist for these two, so each is a tiny toy model
trained for a few seconds on random data, just to show how it works.

Install:
    pip install torch

Run:
    python aae_adaptive_ae_demo.py
"""

import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn

# ---------------------------------------------------------------------------
# Adversarial Autoencoder (AAE) - toy, trained on the spot
# Task: encode/decode a sample and report reconstruction error
# ---------------------------------------------------------------------------
print("\n=== AAE: toy demo ===")

encoder = nn.Sequential(nn.Linear(20, 8), nn.ReLU())
decoder = nn.Sequential(nn.Linear(8, 20))
discriminator = nn.Sequential(nn.Linear(8, 1), nn.Sigmoid())

opt = torch.optim.Adam(
    list(encoder.parameters()) + list(decoder.parameters()) + list(discriminator.parameters()),
    lr=0.01,
)

data = torch.randn(64, 20)
for step in range(50):
    opt.zero_grad()
    z = encoder(data)
    recon = decoder(z)
    recon_loss = torch.mean((recon - data) ** 2)
    prior = torch.randn_like(z)
    d_real = discriminator(prior)
    d_fake = discriminator(z)
    adv_loss = -torch.mean(torch.log(d_real + 1e-6) + torch.log(1 - d_fake + 1e-6))
    loss = recon_loss + 0.1 * adv_loss
    loss.backward()
    opt.step()

sample = torch.randn(1, 20)
predicted = decoder(encoder(sample))
print("reconstruction error on new sample:", round(torch.mean((predicted - sample) ** 2).item(), 4))


# ---------------------------------------------------------------------------
# Adaptive Autoencoder - toy, latent size adapts to input variance
# Task: encode/decode a sample and report reconstruction error
# ---------------------------------------------------------------------------
print("\n=== Adaptive Autoencoder: toy demo ===")

sample = torch.randn(1, 20) * 3
latent_dim = 4 if sample.var().item() < 1.0 else 12  # "adapts" to the input

encoder2 = nn.Sequential(nn.Linear(20, latent_dim), nn.ReLU())
decoder2 = nn.Sequential(nn.Linear(latent_dim, 20))

z = encoder2(sample)
recon = decoder2(z)
print("chosen latent dim:", latent_dim)
print("reconstruction error:", round(torch.mean((recon - sample) ** 2).item(), 4))