from langchain_core.output_parsers import JsonOutputParser
from pyopengenai.query_master import SearchRetriever

from langchain_ollama import ChatOllama


llm = ChatOllama(model = "qwen2.5:1.5b-instruct",
                 temperature = 0,
                 num_predict=8_000)


query  = "example of polymorphism in python"

from pyopengenai.query_master.query_refiner import QueryRefiner



refined_query = QueryRefiner.refine_query(llm = llm,query=query)
print(f"Refined Query: {refined_query}")

# Performing Google search
query_splits= ai_splits(refined_query)
print(f"Query splits: {query_splits}")

exit()

retriever = SearchRetriever(
chunk_overlap = 20,
chunk_size = 200,
max_urls = 5
)

results = retriever.query_based_content_retrieval(
    "example of polymorphism in python")
print(results.urls)
print("\n".join(results.topk_chunks))
