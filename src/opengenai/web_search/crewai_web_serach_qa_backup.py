import asyncio
import time
from typing import List
from langchain_core.language_models import BaseChatModel
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .agent import WebSearchAgent, OptimizedMultiQuerySearcher
from .html_parser import FastHTMLParserV3
from .text_filter import TextFilter
from ..langchain_ollama import CustomChatOllama


class CrewAIWebSearchQASystem:
    def __init__(self, llm: BaseChatModel):
        self._llm = llm
        self._web_agent = WebSearchAgent()
        self._setup_chain()

    def _setup_chain(self):
        prompt = PromptTemplate(
            input_variables=["question", "search_results"],
            template="""
            You are an AI research assistant. Use the following search results to answer the question.
            Question: {question}
            Search Results: {search_results}
            Please provide a concise and accurate answer based on the search results.
            """
        )
        self._chain = prompt | self._llm | StrOutputParser()

    async def _web_search(self, query: str) -> str:
        """Run query through GoogleSearch and parse result."""
        refined_queries = self._web_agent.refine_queries(user_query=query, num_queries=3, llm=self._llm)
        searcher = OptimizedMultiQuerySearcher(max_workers=4)
        results = await searcher.search_multiple_queries(
            queries=refined_queries
        )

        all_urls = [res.urls for res in results]
        non_empty_urls = [x for x in all_urls if x]
        filtered_urls = [y for x in zip(*non_empty_urls) for y in x]

        parser = FastHTMLParserV3(urls=filtered_urls[:10])
        content = await parser.fetch_content()
        filtered_content = [TextFilter.filter_text(c) for c in content[:3] if c]
        return "\n".join(filtered_content)

    async def answer_question(self, question: str) -> str:
        search_results = await self._web_search(question)

        response = await self._chain.ainvoke({
            "question": question,
            "search_results": search_results
        })

        return response.strip()

    async def run_question_answering_loop(self):
        while True:
            user_question = input("Enter your question: \n")
            answer = await self.answer_question(user_question)
            print('#' * 40)
            print(answer)
            print('-' * 40)


# Example usage
if __name__ == "__main__":
    llm = CustomChatOllama(
        model="qwen2:7b-instruct",
        base_url="http://192.168.162.49:8888",
        temperature=0
    )
    qa_system = CrewAIWebSearchQASystem(llm=llm)

    question = "Latest langchain new version improvements?"
    answer = asyncio.run(qa_system.answer_question(question))
    print(answer)

    # Uncomment to run in loop mode
    # asyncio.run(qa_system.run_question_answering_loop())