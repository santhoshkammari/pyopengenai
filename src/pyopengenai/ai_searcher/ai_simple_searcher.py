from langchain_core.language_models import BaseChatModel
from ..query_master import SearchQueryToNSubquery,SearchRetriever,QueryRefiner

class AdvancedAISearcher:
    @classmethod
    def search(cls, llm: BaseChatModel, query: str)-> str:
        refined_query = QueryRefiner.refine_query(llm=llm, query=query)
        query_splits = SearchQueryToNSubquery.ai_splits(llm=llm, query=refined_query)
        retriever = SearchRetriever()
        ans = ""
        all_urls = []
        for chunk in query_splits.get("refined_splits", []):
            results = retriever.query_based_content_retrieval(chunk)
            ans += "\n".join(results.topk_chunks)
            all_urls.extend(results.urls)
        join_urls = "\n".join(all_urls)
        final_ans = f"Answer:\n{ans}\n\nURLs:\n{join_urls}"
        return final_ans