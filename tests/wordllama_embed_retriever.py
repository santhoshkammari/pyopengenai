from langchain_ollama import ChatOllama
from pyopengenai.ai_searcher import AdvancedAISearcher
from src.pyopengenai import CustomChatOllama


llm = ChatOllama(model = "qwen2.5:1.5b-instruct",
                 temperature = 0,
                 num_predict=8_000)
query  = "explain me Design of ACM , better if we use arxiv paper"
rtr  = AdvancedAISearcher(
    max_urls=1
)
print(rtr.generate_final_answer(llm, query,verbose=True))

