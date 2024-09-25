from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser


class SearchQueryToNSubquery:
    @classmethod
    def ai_splits(self,llm: BaseChatModel,query: str) -> dict:
        messages = [
            {"role": "system",
             "content": "You are expert at understanding user query and generating list of google search queries out of them ,"
                        "that completely solves the given user query."
                        "Refine and expand the query into a list of sub-queries"
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