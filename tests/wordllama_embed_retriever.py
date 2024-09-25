from langchain_ollama import ChatOllama
from pyopengenai.ai_searcher import AdvancedAISearcher

llm = ChatOllama(model = "qwen2.5:1.5b-instruct",
                 temperature = 0,
                 num_predict=8_000)
query  = "i want KQML multiagent query language algorithm better to search in arxiv papers"

ans = AdvancedAISearcher.search(llm, query)
print(ans)


