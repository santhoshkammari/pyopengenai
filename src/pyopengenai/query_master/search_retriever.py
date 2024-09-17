import json
from wordllama import WordLlama
from ..researcher_ai import RealTimeGoogleSearchProvider, UrlTextParser
from .text_splitter import TextProcessor


class SearchRetriever:
    def __init__(self):
        self.parser = UrlTextParser()
        self.searcher = RealTimeGoogleSearchProvider()
        self.splitter = WordLlama.load()

    def fetch_and_store_search_results(self, query, file_name_json):
        urls = self.searcher.perform_search(query)
        contents = self.parser.parse_html(urls)
        with open(file_name_json, "w", encoding='utf-8') as f:
            json.dump(contents, f, indent=2)

    def query_based_content_retrieval(self, query, topk=10, return_urls=False):
        urls = self.searcher.perform_search(query)
        contents = self.parser.parse_html(urls)
        splits = TextProcessor.tokenize_list(contents)
        tokens = self.splitter.topk(query, splits, topk)
        if return_urls:
            return tokens, urls
        return tokens


# Example usage
if __name__ == "__main__":
    retriever = SearchRetriever()

    # Fetch and store search results
    retriever.fetch_and_store_search_results("Python programming", "search_results.json")

    # Query-based content retrieval
    results = retriever.query_based_content_retrieval("Object-oriented programming in Python", topk=5)
    print(results)