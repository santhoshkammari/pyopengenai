from src.pyopengenai import ai_search

res = ai_search(
    "give me python code to run latest qwen release 7b model i want to run for chat so please select that  model in huggingface",
    True)
print(res)