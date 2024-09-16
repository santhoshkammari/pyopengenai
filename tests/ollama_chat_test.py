
from src.pyopengenai.langchain_ollama import CustomChatOllama

llm = CustomChatOllama(model="qwen2:0.5b", base_url="http://192.168.162.49:8888")
print(llm.invoke("who are you?").content)

