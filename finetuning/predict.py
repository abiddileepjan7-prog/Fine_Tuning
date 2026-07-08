"""
Run inference with the fine-tuned model saved in ./saved_model.

Usage:
    python predict.py                                  # interactive prompt
    python predict.py "This movie was absolutely great!"  # single input from CLI
"""

import sys
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = "saved_model"
MAX_LENGTH = 256


def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.to(device)
    model.eval()
    return tokenizer, model, device


def predict(text, tokenizer, model, device):
    inputs = tokenizer(
        text,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).squeeze()

    pred_id = int(torch.argmax(probs))
    label = model.config.id2label[pred_id]
    confidence = float(probs[pred_id])
    return label, confidence, probs.tolist()


def main():
    tokenizer, model, device = load_model()
    print(f"Model loaded from ./{MODEL_DIR} on {device}\n")

    # Mode 1: single input given as a CLI argument
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        label, confidence, probs = predict(text, tokenizer, model, device)
        print(f"Input: {text}")
        print(f"Prediction: {label}  (confidence: {confidence:.4f})")
        print(f"Probabilities -> negative: {probs[0]:.4f} | positive: {probs[1]:.4f}")
        return

    # Mode 2: interactive loop
    print("Enter a review to classify (type 'quit' or 'exit' to stop):")
    while True:
        text = input("\n> ").strip()
        if text.lower() in {"quit", "exit"}:
            break
        if not text:
            continue
        label, confidence, probs = predict(text, tokenizer, model, device)
        print(f"Prediction: {label}  (confidence: {confidence:.4f})")
        print(f"Probabilities -> negative: {probs[0]:.4f} | positive: {probs[1]:.4f}")


if __name__ == "__main__":
    main()
