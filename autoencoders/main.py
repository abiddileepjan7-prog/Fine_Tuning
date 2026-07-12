"""
sae_vae_demo.py
================
Pretrained models: Sparse Autoencoder (SAE) and Variational Autoencoder (VAE).

Install:
    pip install torch sae-lens transformer-lens diffusers pillow torchvision

Run:
    python sae_vae_demo.py
"""

import warnings
warnings.filterwarnings("ignore")

import torch

# ---------------------------------------------------------------------------
# Sparse Autoencoder (SAE) - pretrained on GPT-2 activations
# Task: find the strongest sparse feature for a sentence
# ---------------------------------------------------------------------------
print("\n=== SAE: sparse feature prediction ===")
from transformer_lens import HookedTransformer
from sae_lens import SAE

gpt2 = HookedTransformer.from_pretrained("gpt2")
sae, _, _ = SAE.from_pretrained(release="gpt2-small-res-jb", sae_id="blocks.8.hook_resid_pre")

text = "The stock market rallied after the interest rate announcement."
tokens = gpt2.to_tokens(text)
_, cache = gpt2.run_with_cache(tokens)
activations = cache["blocks.8.hook_resid_pre"]

feature_acts = sae.encode(activations)
top_feature = int(feature_acts[0, -1].argmax())
top_value = float(feature_acts[0, -1, top_feature])

print("input:", text)
print("strongest feature id:", top_feature, "| activation:", round(top_value, 4))


# ---------------------------------------------------------------------------
# Variational Autoencoder (VAE) - pretrained Stable Diffusion image VAE
# Task: encode an image to a latent vector and reconstruct it
# ---------------------------------------------------------------------------
print("\n=== VAE: image reconstruction ===")
from diffusers import AutoencoderKL
from PIL import Image, ImageDraw
from torchvision import transforms

vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")
vae.eval()

image = Image.new("RGB", (256, 256), color=(200, 200, 200))
ImageDraw.Draw(image).ellipse((60, 60, 180, 180), fill=(30, 120, 200))
img_tensor = transforms.ToTensor()(image).unsqueeze(0) * 2 - 1

with torch.no_grad():
    latent = vae.encode(img_tensor).latent_dist.sample()
    reconstruction = vae.decode(latent).sample

recon_error = torch.mean((img_tensor - reconstruction) ** 2).item()
print("latent shape:", tuple(latent.shape))
print("reconstruction MSE:", round(recon_error, 6))

# Save original and reconstructed images to disk so you can compare them.
recon_image = transforms.ToPILImage()((reconstruction.squeeze(0).clamp(-1, 1) + 1) / 2)
image.save("vae_original.png")
recon_image.save("vae_reconstructed.png")
print("saved: vae_original.png, vae_reconstructed.png")