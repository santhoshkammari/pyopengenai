from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from pyopengenai import QueryRefiner, SearchQueryToNSubquery
from pyopengenai.query_master import SearchRetriever

from langchain_ollama import ChatOllama


llm = ChatOllama(model = "qwen2.5:1.5b-instruct",
                 temperature = 0,
                 num_predict=8_000)
query  = "i want KQML multiagent query language explanation"




