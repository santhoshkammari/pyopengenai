from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser


class SearchQueryToNSubquery:
    @classmethod
    def ai_splits(self,llm: BaseChatModel,query: str,n_splits: int | None = None) -> dict:
        if n_splits is None:
            n_splits = ""
        messages = [
            {"role": "system",
             "content": "You are expert at understanding user query and generating list of google search queries rephrase and rewritten for better search results ,"
                        "that completely solves the given user query."
                        f"Refine and expand the query , then generate the {n_splits}variations of the query"
                        "Output JSON format: {\"refined_splits\":[<list_of_better_google_search_queries>]}"},
            {"role": "user", "content": f"Query: {query}"}
        ]
        results = llm.invoke(messages).content

        try:
            output_parser = JsonOutputParser()
            parsed_results = output_parser.parse(results)
        except:
            return {'refined_splits':[]}
        return parsed_results