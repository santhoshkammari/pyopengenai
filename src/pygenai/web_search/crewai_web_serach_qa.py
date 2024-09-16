import asyncio
import time

from crewai import Agent, Task, Crew
from langchain.tools import Tool
from langchain_core.language_models import BaseChatModel

from .agent import WebSearchAgent, OptimizedMultiQuerySearcher
from .html_parser import FastHTMLParserV3
from ..langchain_ollama import CustomChatOllama
from .text_filter import TextFilter



class CrewAIWebSearchQASystem:
    def __init__(self,llm:BaseChatModel):
        self._llm = llm
        self._search_tool = None
        self._researcher = None
        self._setup_tool_and_search()


    def _web_search(self,query: str) -> str:
        """Run query through GoogleSearch and parse result."""
        web_agent = WebSearchAgent()
        rq = web_agent.refine_queries(user_query=query,num_queries=3,llm=self._llm)
        with OptimizedMultiQuerySearcher(max_workers=4) as searcher:
            results = asyncio.run(searcher.search_multiple_queries(queries=rq,
                                                                   search_provider="google"))
        all_urls = [res.urls for res in results]
        non_empty_urls = [x for x in all_urls if x]
        filtered_urls = [y for x in zip(*non_empty_urls) for y in x]

        parser = FastHTMLParserV3(urls=filtered_urls[:10])
        content = asyncio.run(parser.fetch_content())
        content = [TextFilter.filter_text(c) for c in content[:3] if c]

        return "\n".join(content)


    # Function to create a task based on the user's question
    def _create_search_task(self,question):

        return Task(
            description=f"Research the following question: {question}",
            expected_output="A single line answer to the question",
            agent=self._researcher
        )

    # Function to run the crew and get results
    def run_question_answering(self,question):
        task = self._create_search_task(question)
        crew = Crew(
            agents=[self._researcher],
            tasks=[task]
        )
        result = crew.kickoff()
        return result

    def run_question_answering_loop(self):
        while True:
            user_question = input("Enter your question: \n")
            results = self.run_question_answering(user_question)
            print('#'*40)
            print(results)
            print('-'*40)

    def _setup_tool_and_search(self):
        self._search_tool = Tool(
            name="Google Search",
            func=self._web_search,
            description="Useful for when you need to answer questions about current events or the current state of the world"
        )
        self._researcher = Agent(
            role='Researcher',
            goal='Find accurate and up-to-date information',
            backstory='You are an AI research assistant skilled in finding information on the internet.',
            tools=[self._search_tool],
            llm=self._llm,
            verbose = True
        )


# Example usage
if __name__ == "__main__":
    llm = CustomChatOllama(
        model="qwen2:7b-instruct",
        base_url="http://192.168.162.49:8888",
        temperature=0
    )
    crew = CrewAIWebSearchQASystem(llm=llm)
    print(crew.run_question_answering(question="Latest langchain new version improvements?"))

