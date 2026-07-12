import csv
import json
import time

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
FINETUNED_MODEL_DIR = "./qwen_qlora_merged"   # output of merge_lora.py
TEST_FILE = "test_split.jsonl"
NUM_TEST_PROMPTS = 20          # keep small -- CPU generation is slow
MAX_NEW_TOKENS = 150
RESULTS_CSV = "inference_results.csv"

torch.set_num_threads(psutil.cpu_count(logical=True))


def current_rss_gb():
    return psutil.Process().memory_info().rss / 1e9


def load_model(path_or_name):
    mem_before = current_rss_gb()
    start = time.time()
    tokenizer = AutoTokenizer.from_pretrained(path_or_name)
    model = AutoModelForCausalLM.from_pretrained(
        path_or_name,
        torch_dtype=torch.float32,   # plain CPU inference, no quantization
    )
    model.eval()
    load_time = time.time() - start
    mem_after = current_rss_gb()
    print(f"Loaded {path_or_name} in {load_time:.1f}s, "
          f"RAM used: {mem_after - mem_before:.2f} GB")
    return model, tokenizer, load_time, mem_after - mem_before


def generate(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    start = time.time()
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,          # greedy, so base vs fine-tuned is a fair comparison
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.time() - start
    new_tokens = output_ids.shape[1] - inputs["input_ids"].shape[1]
    text = tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    tokens_per_sec = new_tokens / elapsed if elapsed > 0 else 0.0
    return text, elapsed, new_tokens, tokens_per_sec


def main():
    test_rows = []
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            test_rows.append(json.loads(line))
    test_rows = test_rows[:NUM_TEST_PROMPTS]

    print("=== Loading base (un-fine-tuned) model ===")
    base_model, base_tok, base_load_time, base_load_mem = load_model(BASE_MODEL_NAME)

    print("=== Loading fine-tuned (merged) model ===")
    ft_model, ft_tok, ft_load_time, ft_load_mem = load_model(FINETUNED_MODEL_DIR)

    rows = []
    for i, row in enumerate(test_rows):
        prompt = row["prompt"]
        reference = row["output"]

        base_text, base_time, base_ntok, base_tps = generate(base_model, base_tok, prompt)
        ft_text, ft_time, ft_ntok, ft_tps = generate(ft_model, ft_tok, prompt)

        print(f"[{i+1}/{len(test_rows)}] base {base_time:.1f}s ({base_tps:.1f} tok/s) | "
              f"finetuned {ft_time:.1f}s ({ft_tps:.1f} tok/s)")

        rows.append({
            "instruction": row["instruction"],
            "input": row["input"],
            "reference_output": reference,
            "base_output": base_text,
            "base_latency_sec": base_time,
            "base_tokens_per_sec": base_tps,
            "finetuned_output": ft_text,
            "finetuned_latency_sec": ft_time,
            "finetuned_tokens_per_sec": ft_tps,
        })

    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved per-prompt results to {RESULTS_CSV}")
    print("\n--- Loading summary ---")
    print(f"Base model load time: {base_load_time:.1f}s, RAM: {base_load_mem:.2f} GB")
    print(f"Fine-tuned model load time: {ft_load_time:.1f}s, RAM: {ft_load_mem:.2f} GB")

    with open("loading_summary.json", "w") as f:
        json.dump({
            "base_load_time_sec": base_load_time,
            "base_load_ram_gb": base_load_mem,
            "finetuned_load_time_sec": ft_load_time,
            "finetuned_load_ram_gb": ft_load_mem,
        }, f, indent=2)


if __name__ == "__main__":
    main()

