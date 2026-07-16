import time, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def time_model(model_dir, tokenizer, question="Give three tips for staying healthy."):
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32)
    model.eval()
    load_time = time.time() - t0

    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": question}], tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt")

    t0 = time.time()
    out = model.generate(**inputs, max_new_tokens=150, do_sample=False,
                          pad_token_id=tokenizer.eos_token_id)
    infer_time = time.time() - t0

    return load_time, infer_time

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

base_load, base_infer = time_model("Qwen/Qwen2.5-0.5B-Instruct", tokenizer)
ft_load, ft_infer = time_model("./qwen-merged", tokenizer)

print(f"BASE      -> load: {base_load:.2f}s | inference: {base_infer:.2f}s")
print(f"FINE-TUNED-> load: {ft_load:.2f}s | inference: {ft_infer:.2f}s")