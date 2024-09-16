import asyncio
import re
from io import BytesIO
from typing import List, Dict, Union, Any
from datetime import datetime
import json
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from weasyprint import HTML
import markdown
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain.schema import StrOutputParser
from .optimized_multi_query_searcher import OptimizedMultiQuerySearcher

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebSearchHelper:
    @staticmethod
    def clean_query(query: str, query_with_date: bool = False) -> str:
        if not query:
            return query
        query = re.sub(r'[^a-zA-Z0-9\s]', '', query)

        if query_with_date:
            today_date = ", " + datetime.now().strftime('%B-%d-%Y')
        else:
            today_date = ""

        query = f"{query}{today_date}"
        return ' '.join(query.split())

    @staticmethod
    def summarize_text(llm, text: str) -> str:
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=250,
            chunk_overlap=25,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)

        summarize_prompt = PromptTemplate.from_template(
            """Summarize the following [CHUNK], focusing on the main points:
            - Maintain key terms and concepts
            - Keep the language natural and easy to understand
            - Do not introduce new information, don't say this text, directly start summary

            [CHUNK]
            {chunk}

            Summary:"""
        )

        summarize_chain = llm | StrOutputParser()
        prompts = [summarize_prompt.format(chunk=chunk) for chunk in chunks]
        summaries: List[str] = summarize_chain.batch(prompts)

        combined_summary = "\n".join(summaries)
        combined_summary = f"### Summary: \n{combined_summary}\n\n"
        combined_summary += f"### Original result: \n{text}\n\n---\n\n"
        return combined_summary

    @staticmethod
    def get_md_content(result,summarize = False):
        md_content = f"# Search Results for: \n{result['user_query']}\n\n"
        md_content += f"## Refined Queries\n\n"
        for query in result['refined_queries']:
            md_content += f"- {query}\n"
        md_content += f"\n## Search Results\n\n"

        for i, search_result in enumerate(result['search_results'], 1):
            if summarize and "no valid content" not in search_result.lower():
                md_content += WebSearchHelper.summarize_text(llm, search_result)
            else:
                md_content += f"### Result {i}\n\n{search_result['results']}\n\n---\n\n"

        md_content += f"\n## URLs\n\n"
        for i, url_list in enumerate(result['search_results'], 1):
            try:
                _query = result['refined_queries'][i - 1]
            except:
                _query = f"Query {i}"
            md_content += f"### {_query}\n\n"
            for url in url_list['urls']:
                md_content += f"- [{url}]({url})\n"
        return md_content

    @staticmethod
    def save_results(result: Dict, base_filename: str = "search_results", summarize: bool = False, llm=None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}"
        # os.makedirs("Results", exist_ok=True)
        # with open(f"Results/{filename}.json", "w") as f:
        #     json.dump(result, f, indent=2)

        md_content = WebSearchHelper.get_md_content(result=result,
                                                    summarize=summarize)



        return md_content

    @staticmethod
    def generate_pdf(md_content):
        html = markdown.markdown(md_content)

        # Add CSS for better URL display
        html = f"""
        <style>
        .url-list {{
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        }}
        .url-list a {{
            display: block;
            margin-bottom: 5px;
            word-break: break-all;
        }}
        </style>
        {html}
        """

        # Create a BytesIO object to store the PDF
        pdf_buffer = BytesIO()

        # Generate the PDF and write it to the BytesIO buffer
        HTML(string=html).write_pdf(pdf_buffer)

        # Get the PDF content as bytes
        pdf_bytes = pdf_buffer.getvalue()

        return pdf_bytes

    @staticmethod
    def get_md_content_v2(search_results,user_query,refined_queries):
        md_content = f"# Search Results for: \n{user_query}\n\n"
        md_content += f"## Refined Queries\n\n"
        for query in refined_queries:
            md_content += f"- {query}\n"
        md_content += f"\n## Search Results\n\n"
        for idx,x in enumerate(search_results):
            md_content += f"### Result{idx}:\n {x['context']}\n\n---\n\n"
        md_content += "## URLS:\n"
        for idx,x in enumerate(search_results,1):
            md_content += f"{idx}:{x['url']}\n\n"

        return md_content





class WebSearchAgentPersonas:
    expert_personas = [
        "100-year-old Data Science Guru",
        "Omniscient Web Search Wizard",
        "AI-powered Research Mastermind"
    ]

    @classmethod
    def get_query_refining_prompt(cls, num_queries: int):
        chosen_persona = " and ".join(cls.expert_personas)

        QUERY_REFINING_PROMPT = f"""You are the {chosen_persona}, a legendary search expert with unparalleled ability to find information on any topic. Your task is to generate {num_queries} highly effective search queries based on the following user query: {{user_query}}

        Guidelines for generating queries:
        1. Analyze the user's intent deeply and break it down into core concepts.
        2. Create queries that cover all aspects of the user's request, including potential implicit needs.
        3. Use advanced search operators when appropriate (e.g., site:github.com, filetype:pdf, intitle:, etc.).
        4. Include specific technical terms, frameworks, or methodologies relevant to the topic.
        5. Consider time-sensitive information by including  "latest" keywords.
        6. Combine broad exploratory queries with highly specific ones to ensure comprehensive coverage.
        7. Anticipate related topics or technologies that might yield valuable results.
        8. Craft queries as if you're an expert in the field, using insider knowledge and terminology.
        9. Ensure each query is unique and adds value beyond the others.
        10. Optimize for both relevance and recency of results.

        Format each query directly don't add extra terms as a separate line, without numbering or additional text."""

        # Format: Return a Python list of strings, each string being a refined search query. Do not include any explanations or numbering."""

        QUERY_REFINING_PROMPT_V2 = """You are an AI-powered search query optimizer. Your task is to analyze the given user query and generate {num_queries} refined search queries that will yield the most relevant and comprehensive results. 

Consider the following aspects when refining the query:
1. Core concepts and potential subtopics
2. Technical terminology and domain-specific language
3. Recent developments and time-sensitive information
4. Different perspectives or applications of the topic
5. Potential data sources or content types (e.g., academic papers, industry reports, code repositories)

For the user query: {user_query}

Generate diverse, effective search queries that capture the essence of the user's information need while expanding its scope to ensure comprehensive coverage. Each query should offer a unique angle or approach to finding relevant information.

Format each query directly as a separate line, each string being a refined search query. Do not include any explanations or numbering."""

        return QUERY_REFINING_PROMPT_V2


class WebSearchAgent:
    def __init__(self,query_refining_prompt=None):
        self.web_fetcher = None
        self.query_refining_prompt = query_refining_prompt

    def refine_queries(self, user_query: str, num_queries: int,llm) -> List[str]:
        if self.query_refining_prompt is None:
            self.query_refining_prompt = WebSearchAgentPersonas.get_query_refining_prompt(num_queries=num_queries)
            # self.query_refining_prompt = self.get_query_refining_prompt()
        query_refinement_prompt = PromptTemplate.from_template(self.query_refining_prompt)
        query_refinement_chain = query_refinement_prompt | llm | StrOutputParser() | (lambda x: x.split("\n"))
        refined_queries = query_refinement_chain.invoke({"user_query": user_query, "num_queries": num_queries})
        refined_queries = [x for x in refined_queries if len(x) > 0]
        return refined_queries

    async def search_web(self, refined_queries: List[str],
                         top_k=5, fast_response=False,
                         chromedriver_path="/usr/local/bin/chromedriver",
                         max_length=None, summarize=False, summary_sentences=3,
                         search_provider="google",
                         num_results=10,
                         url_fetch_timeout=10,
                         extract_url_content=False
                         ):
        logger.info("Searching the web")
        search_results = []


        for query in refined_queries:
            logger.info(f"Searching for: {query}")
            results, search_res = await self.web_fetcher.fetch(query,
                                                               top_k=top_k, fast_response=fast_response,
                                                               chromedriver_path=chromedriver_path,
                                                               max_length=max_length, summarize=summarize,
                                                               summary_sentences=summary_sentences,
                                                               search_provider=search_provider,
                                                               num_results=num_results,
                                                               url_fetch_timeout=url_fetch_timeout,
                                                               extract_url_content=extract_url_content
                                                               )
            if "no valid" in results.strip():
                logger.warning(f"Empty result for query: {query}")
            else:
                logger.info(f"Found results for query: {query}")

            search_results.append(dict(
                results=results,
                urls=search_res.urls,
                top_response=search_res.top_response,
                title_and_links=search_res.title_and_links,
                html_content=search_res.html_content
            ))
        logger.info(f"Completed web search for {len(search_results)} queries")
        return search_results

    async def arun(
            self,
            user_query: str,
            num_queries: Union[None,int] = None,
            llm = None,
            summarize: bool = False,
            summary_sentences: int = 3,
            query_with_date: bool = True,
            top_k: int = 5,
            fast_response: bool = False,
            chromedriver_path: str = "/usr/local/bin/chromedriver",
            max_length: Union[None, int] = None,
            search_provider=None,
            num_results=10,
            url_fetch_timeout=10,
            extract_url_content=False,
            return_markdown_text = True,
            return_json = False
    , return_pdf=False,
            return_only_urls  = False,
            max_workers=None) -> Union[Dict,str,bytes]:
        logger.info(f"Starting web search agent for query: {user_query}")
        if num_queries is not None and llm is None:
            raise ValueError("If num_queries is provided, llm should be provided as well.")
        if summarize is True:
            extract_url_content = True
        if num_queries is not None:
            refined_queries = self.refine_queries(user_query, num_queries,llm)
            refined_queries = [WebSearchHelper.clean_query(query, query_with_date) for query in refined_queries]
        else:
            refined_queries = [user_query]
        logger.info(f"Optimized queries: {refined_queries}")
        gs = OptimizedMultiQuerySearcher(chromedriver_path=chromedriver_path,
                                         max_workers=max_workers)
        all_urls = await gs.search_multiple_queries(refined_queries, search_provider=search_provider)
        # filtered_urls = [each_url for url in all_urls for each_url in url.urls if len(each_url)>0]
        all_urls = [url.urls for url in all_urls]
        filtered_urls = [y for x in zip(*all_urls) for y in x]
        if return_only_urls:
            return filtered_urls
        # res = await WebFetcher.get_url_content(filtered_urls)
        if extract_url_content:
            from opengenai.web_search.html_parser import FastHTMLParserV3
            parser = FastHTMLParserV3(urls=filtered_urls, fast_response=fast_response,
                                      max_length=max_length, summarize=summarize, summary_sentences=summary_sentences)
            contents = await parser.fetch_content(url_fetch_timeout=url_fetch_timeout)
        else:
            contents = [""]*len(filtered_urls)

        search_results = []
        for r,c in zip(filtered_urls,contents):
            search_results.append(dict(
                url=r,
                context = c
            ))

        # search_results = await self.search_web(refined_queries,
        #                                        top_k=top_k, fast_response=fast_response,
        #                                        chromedriver_path=chromedriver_path,
        #                                        max_length=max_length, summarize=summarize,
        #                                        summary_sentences=summary_sentences,
        #                                        search_provider=search_provider,
        #                                        num_results=num_results,
        #                                        url_fetch_timeout=url_fetch_timeout,
        #                                        extract_url_content=extract_url_content
        #                                        )
        md_content = WebSearchHelper.get_md_content_v2(search_results,
                                                       user_query,
                                                       refined_queries)
        # md_content = WebSearchHelper.save_results({
        #     "user_query": user_query,
        #     "refined_queries": refined_queries,
        #     "search_results": search_results
        # }, summarize=summarize, llm=self.llm)
        logger.info("Web search agent completed successfully")
        if return_pdf:
            return WebSearchHelper.generate_pdf(md_content=md_content)

        if return_json:
            return {
                "user_query": user_query,
                "refined_queries": refined_queries,
                "search_results": search_results,
                "md_content": md_content,
            }
        elif return_markdown_text:
            return md_content
        else:
            return md_content

    def get_query_refining_prompt(self):
        QUERY_REFINING_PROMPT = """You are GoogleSearch Expert , Generate {num_queries} different variations search queries based on the following user query: {user_query}

                    Guidelines for generating queries:
                    1. Generate in best form to get almost perfect result for user query
                    2. Add Meaningfull Search Terms to Enrich the Query
                    3. Avoid overly broad or vague queries

                    Format each query directly don't add extra terms as a separate line, without numbering or additional text."""
        return QUERY_REFINING_PROMPT


class WebSearchArguments(BaseModel):
    user_query: str
    num_queries: Union[int,None] = None
    summarize: bool = False
    summary_sentences: int = 3
    query_with_date: bool = True
    top_k: int = 3
    llm:Any = None
    fast_response: bool = False
    chromedriver_path: str = "/usr/local/bin/chromedriver"
    max_length: Union[int, None] = None
    search_provider: Union[None,str] = Field(
        default=None,
        description="Search engine to use for the search. Supported options: google, bing",
    )
    max_workers : int = 4
    num_results: int = 10
    url_fetch_timeout: int = 10
    extract_url_content: bool = False
    return_markdown_text: bool = True,
    return_json: bool = False
    return_pdf:bool = False


# Example usage
if __name__ == "__main__":
    # llm = ChatOllama(model="gemma2:2b")
    from opengenai.langchain_ollama.ollama import CustomChatOllama
    llm  = CustomChatOllama(
        model = "gemma2:2b",
        base_url = "http://192.168.162.49:8888"
    )
    agent = WebSearchAgent()
    args = WebSearchArguments(
        user_query="i want to know the latest agentic RAG based approaches",
        num_queries=3,
        query_with_date=False,
    )
    result = asyncio.run(agent.arun(**args.model_dump()))
    with open("res.md","w",encoding="utf-8") as f:
        f.write(result)
