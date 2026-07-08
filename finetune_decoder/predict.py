"""
Run the fine-tuned SmolLM2 model locally on custom input.

Usage:
    python predict.py                                    # interactive mode
    python predict.py "What is the capital of France?"   # single question
"""

import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_DIR = "smollm2_dolly_finetuned"
SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's instruction accurately and concisely."
MAX_NEW_TOKENS = 200


def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForCausalLM.from_pretrained(MODEL_DIR)
    model.to(device)
    model.eval()
    return tokenizer, model, device


def ask(question, tokenizer, model, device, context=""):
    user_msg = f"{question}\n\nContext:\n{context}" if context.strip() else question
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
    response = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    return response.strip()


def main():
    tokenizer, model, device = load_model()
    print(f"Model loaded from ./{MODEL_DIR} on {device}\n")

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        answer = ask(question, tokenizer, model, device)
        print(f"Q: {question}")
        print(f"A: {answer}")
        return

    print("Type a question (or 'quit' to exit):")
    while True:
        question = input("\n> ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        answer = ask(question, tokenizer, model, device)
        print(f"A: {answer}")


if __name__ == "__main__":
    main()