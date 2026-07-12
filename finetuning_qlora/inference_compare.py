import json

import pandas as pd
from rouge_score import rouge_scorer
import sacrebleu

RESULTS_CSV = "inference_results.csv"
LOADING_SUMMARY = "loading_summary.json"


def score_column(df, output_col, reference_col="reference_output"):
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    rouge1, rouge2, rougeL, bleu_scores = [], [], [], []
    for ref, hyp in zip(df[reference_col], df[output_col]):
        ref, hyp = str(ref), str(hyp)
        scores = scorer.score(ref, hyp)
        rouge1.append(scores["rouge1"].fmeasure)
        rouge2.append(scores["rouge2"].fmeasure)
        rougeL.append(scores["rougeL"].fmeasure)
        bleu_scores.append(sacrebleu.sentence_bleu(hyp, [ref]).score)

    return {
        "rouge1": sum(rouge1) / len(rouge1),
        "rouge2": sum(rouge2) / len(rouge2),
        "rougeL": sum(rougeL) / len(rougeL),
        "bleu": sum(bleu_scores) / len(bleu_scores),
    }


def main():
    df = pd.read_csv(RESULTS_CSV)

    base_scores = score_column(df, "base_output")
    ft_scores = score_column(df, "finetuned_output")

    print("=== Text quality metrics (vs. reference outputs) ===")
    print(f"{'Metric':<10}{'Base':>10}{'Fine-tuned':>14}")
    for metric in ["rouge1", "rouge2", "rougeL", "bleu"]:
        print(f"{metric:<10}{base_scores[metric]:>10.4f}{ft_scores[metric]:>14.4f}")

    print("\n=== Latency / speed (CPU inference) ===")
    print(f"Base avg latency:       {df['base_latency_sec'].mean():.2f} sec/prompt, "
          f"{df['base_tokens_per_sec'].mean():.2f} tok/s")
    print(f"Fine-tuned avg latency: {df['finetuned_latency_sec'].mean():.2f} sec/prompt, "
          f"{df['finetuned_tokens_per_sec'].mean():.2f} tok/s")

    try:
        with open(LOADING_SUMMARY) as f:
            loading = json.load(f)
        print("\n=== Model loading (CPU) ===")
        print(f"Base:       {loading['base_load_time_sec']:.1f}s, "
              f"{loading['base_load_ram_gb']:.2f} GB RAM")
        print(f"Fine-tuned: {loading['finetuned_load_time_sec']:.1f}s, "
              f"{loading['finetuned_load_ram_gb']:.2f} GB RAM")
    except FileNotFoundError:
        pass

    summary_rows = [
        {"model": "base", **base_scores,
         "avg_latency_sec": df["base_latency_sec"].mean(),
         "avg_tokens_per_sec": df["base_tokens_per_sec"].mean()},
        {"model": "finetuned", **ft_scores,
         "avg_latency_sec": df["finetuned_latency_sec"].mean(),
         "avg_tokens_per_sec": df["finetuned_tokens_per_sec"].mean()},
    ]
    pd.DataFrame(summary_rows).to_csv("evaluation_summary.csv", index=False)
    print("\nSaved evaluation_summary.csv")


if __name__ == "__main__":
    main()

