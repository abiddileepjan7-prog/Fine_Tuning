from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="mrm8488/deberta-v3-small-finetuned-sst2"
)

text = "I absolutely loved this movie."

print(classifier(text))