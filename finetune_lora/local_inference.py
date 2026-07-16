import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"# original model (before fine-tuning)
FINETUNED_DIR = "./qwen-merged"                 # your fine-tuned merged model (after fine-tuning)

QUESTION = "Give three tips for staying healthy."

# Load the tokenizer once from the base model. The tokenizer itself wasn't
# changed during LoRA fine-tuning, only the model weights were — so we reuse
# this same tokenizer for both models. This also avoids a tokenizer_config.json
# format mismatch that can happen when the config was saved by a newer/older
# version of transformers (e.g. saved on Colab, loaded locally).
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)


def ask(model_dir, question):
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32)
    model.eval()

    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": question}],
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )
    answer = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return answer


if __name__ == "__main__":
    print("Question:", QUESTION)

    print("\n=== BEFORE fine-tuning (base model) ===")
    print(ask(BASE_MODEL_ID, QUESTION))

    print("\n=== AFTER fine-tuning (merged model) ===")
    print(ask(FINETUNED_DIR, QUESTION))