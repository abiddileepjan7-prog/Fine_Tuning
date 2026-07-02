

from transformers import pipeline

summarizer = pipeline(
    "summarization",
    model="allenai/led-base-16384"
)
text = """
Artificial Intelligence (AI) is a branch of computer science that focuses on
creating machines capable of performing tasks that typically require human
intelligence. These tasks include learning from data, recognizing speech,
understanding natural language, making decisions, and solving complex problems.
AI has become an essential technology in industries such as healthcare,
finance, transportation, education, and manufacturing. In healthcare, AI helps
doctors diagnose diseases more accurately. In finance, it detects fraudulent
transactions and predicts market trends. Self-driving cars use AI to navigate
roads safely. As AI continues to evolve, it is expected to improve productivity,
reduce human effort, and create new opportunities across various industries.
"""

summary = summarizer(
    text,
    max_length=120,
    min_length=40,
    do_sample=False
)

print(summary[0]["summary_text"])