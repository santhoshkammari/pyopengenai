
from src.opengenai.langchain_ollama import CustomChatOllama

llm = CustomChatOllama(model="gemma2:2b", base_url="http://192.168.162.49:8888")
print(llm.invoke("who are you?").content)

