from src.pyopengenai import google_search

res = google_search(
    "give me python code to run qwen2 model in huggingface",
    True)
print(res)