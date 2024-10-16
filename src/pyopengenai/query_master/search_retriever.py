import json

from pydantic import BaseModel
from wordllama import WordLlama
from ..researcher_ai import RealTimeGoogleSearchProvider, UrlTextParser
from .text_splitter import TextProcessor


class SearchRetrieverResult(BaseModel):
    topk_chunks: list = []
    urls: list = []
    all_contents: list = []
    all_splits: list = []


class SearchRetriever:
    def __init__(self,chunk_overlap = 25,
chunk_size = 250,
max_urls = 5,
                 extract_pdf=True):
        self.chunk_overlap = chunk_overlap
        self.chunk_size = chunk_size
        self.max_urls = max_urls
        self.parser = UrlTextParser(extract_pdf=extract_pdf)
        self.searcher = RealTimeGoogleSearchProvider()
        self.splitter = WordLlama.load()

    def fetch_and_store_search_results(self, query, file_name_json):
        urls = self.searcher.perform_search(query,max_urls=self.max_urls)
        contents = self.parser.parse_html(urls)
        with open(file_name_json, "w", encoding='utf-8') as f:
            json.dump(contents, f, indent=2)

    def query_based_content_retrieval(self, query, topk=10, return_urls=False,
                                      verbose = False):
        urls = self.searcher.perform_search(query,max_urls=self.max_urls)
        if verbose:
            print(f"URLs found: {urls}")
        contents = self.parser.parse_html(urls)
        if verbose:
            print(f"len of contents: {len(contents)}")

        splits = TextProcessor.tokenize_list(contents,chunk_size=self.chunk_size,
                                             chunk_overlap=self.chunk_overlap)
        if verbose:
            print(f"len of splits: {len(splits)}")
        tokens = self.splitter.topk(query, splits, min(topk, len(splits)-1)) if len(splits)>2 else []
        if return_urls:
            return tokens, urls
        return SearchRetrieverResult(
            topk_chunks=tokens,
            urls=urls,
            all_contents=contents,
            all_splits = splits
        )


# Example usage
if __name__ == "__main__":
    retriever = SearchRetriever()

    # Fetch and store search results
    retriever.fetch_and_store_search_results("Python programming", "search_results.json")

    # Query-based content retrieval
    results = retriever.query_based_content_retrieval("Object-oriented programming in Python", topk=5)
    print(results)