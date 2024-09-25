from langchain_core.output_parsers import JsonOutputParser
from pyopengenai import QueryRefiner, SearchQueryToNSubquery
from pyopengenai.query_master import SearchRetriever

from langchain_ollama import ChatOllama


llm = ChatOllama(model = "qwen2.5:1.5b-instruct",
                 temperature = 0,
                 num_predict=8_000)
query  = "i want KQML multiagent query language explanation"

refined_query = QueryRefiner.refine_query(llm = llm,query=query)
print(f"Refined Query: {refined_query}")

# Performing Google search
query_splits= SearchQueryToNSubquery.ai_splits(llm=llm,query=refined_query)
print(f"Query splits: {query_splits}")

retriever = SearchRetriever(
chunk_overlap = 20,
chunk_size = 100,
max_urls = 5
)
ans = ""
for chunk in query_splits.get("refined_splits",[]):
    results = retriever.query_based_content_retrieval(chunk)
    print(results.urls)
    ans +="\n".join(results.topk_chunks)
    print(ans)
