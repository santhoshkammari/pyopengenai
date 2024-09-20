from src.pyopengenai import CustomChatOllama

llm = CustomChatOllama()

messages = [
    {"role":"system","content":"You are Ai Assistant"},
    {"role":"user","content":"what is capital of france?"}
]

print(llm.invoke(messages).content)
