import os
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_NAME = "microsoft/deberta-v3-small"
DATA_PATH = os.path.join("data", "IMDB_Dataset.csv")
OUTPUT_DIR = "saved_model"
CHECKPOINT_DIR = "results"
MAX_LENGTH = 256
TEST_SIZE = 0.2
SEED = 42
N_TRAIN = 5000
N_TEST = 500

NUM_EPOCHS = 1
TRAIN_BATCH_SIZE = 4       
EVAL_BATCH_SIZE = 16
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.06

LABEL2ID = {"negative": 0, "positive": 1}
ID2LABEL = {0: "negative", 1: "positive"}


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["label"] = df["sentiment"].map(LABEL2ID)
    df = df[["review", "label"]].rename(columns={"review": "text"})

    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=SEED,
        stratify=df["label"],
    )

    # Subsample for a faster run, keeping class balance
    train_df, _ = train_test_split(
        train_df,
        train_size=N_TRAIN,
        random_state=SEED,
        stratify=train_df["label"],
    )
    test_df, _ = train_test_split(
        test_df,
        train_size=N_TEST,
        random_state=SEED,
        stratify=test_df["label"],
    )

    print(f"Train size: {len(train_df)} | Test size: {len(test_df)}")
    return Dataset.from_pandas(train_df.reset_index(drop=True)), Dataset.from_pandas(
        test_df.reset_index(drop=True)
    )

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary"
    )
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    train_ds, test_ds = load_data()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_fn(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_LENGTH,
        )

    train_ds = train_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    test_ds = test_ds.map(tokenize_fn, batched=True, remove_columns=["text"])

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    # Full fine-tuning: make sure every parameter is trainable.
    for param in model.parameters():
        param.requires_grad = True

    training_args = TrainingArguments(
        output_dir=CHECKPOINT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=EVAL_BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=os.path.join(CHECKPOINT_DIR, "logs"),
        logging_steps=50,
        fp16=torch.cuda.is_available(),  # mixed precision only if a GPU is present
        report_to="none",
        seed=SEED,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    print("\nFinal evaluation on test set:")
    metrics = trainer.evaluate()
    print(metrics)

    # Save the final model + tokenizer for later inference
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nModel saved to ./{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
