import asyncio
from langchain_ollama import ChatOllama
from opengenai.web_search import WebSearchAgent,WebSearchArguments,FastHTMLParserV3,OptimizedMultiQuerySearcher

from opengenai.langchain_ollama import CustomChatOllama
llm = ChatOllama(model="qwen2:0.5b")
llm = CustomChatOllama(
    model = "qwen2:7b-instruct",
    base_url = "http://192.168.162.49:8888",
    temperature = 0
)
from opengenai.langchain_ollama.ollama import CustomChatOllama

# llm = CustomChatOllama(
#     model="gemma2:2b",
#     base_url="http://192.168.162.49:8888"
# )
agent = WebSearchAgent()
args = WebSearchArguments(
    user_query="i want to know the latest agentic RAG based approaches",
    num_queries=5,
    llm = llm,
    query_with_date=False,
    extract_url_content=True
)
result = asyncio.run(agent.arun(**args.model_dump()))
from pathlib import Path
Path("results.txt").write_text(result)
