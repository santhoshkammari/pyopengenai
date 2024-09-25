from pyopengenai.query_master import SearchRetriever

retriever = SearchRetriever(
chunk_overlap = 20,
chunk_size = 200,
max_urls = 5
)
results = retriever.query_based_content_retrieval(
    "example of polymorphism in python")
print(results.urls)
print("\n".join(results.topk_chunks))
