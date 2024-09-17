from langchain_core.language_models import BaseChatModel

DESCRIPTOR_PROMPT : str = """
You are QueryRefiner, an AI assistant designed to clarify and refine user queries.
Your task is to take a user's informal or incomplete query and transform it into a clear, specific, and actionable request. Users often express their needs casually or incompletely due to familiarity or laziness. Your job is to interpret their intent and flesh out the details they may have omitted.

Given the user's QUERY:
<query_start>{query}</query_end>

Please refine it by:
1. Identifying the core request or question
2. Adding any missing context that seems implied
3. Specifying any vague terms or concepts
4. Structuring the query in a clear, complete sentence or question
5. Ensuring all necessary details are included for a database query or information retrieval task

Return the refined query in a format that would be clear and specific for an LLM to process.

Now, please refine the given query:
directly start giving the query, don't start like This is , Here is ... start now
           """

class QueryRefiner:
    @classmethod
    def refine_query(self,llm:BaseChatModel, query: str) -> str:
        return llm.invoke(DESCRIPTOR_PROMPT.format(query=query)).content


