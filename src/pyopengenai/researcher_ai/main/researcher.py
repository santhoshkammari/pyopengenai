from .parse_url.html_parser import UrlTextParser
from .search_provider.searcher import RealTimeGoogleSearchProvider

class AiResearcher:
    searcher = RealTimeGoogleSearchProvider()
    parser = UrlTextParser()

    def get_query_content(self,query,max_articles = 3,max_urls=6):
        """
        Gets the top 3 URLs for the given query, fetches their content,
        returns the first three contents.'
        """
        urls = self.searcher.perform_search(query,
                                       max_urls=max_urls)
        urls = list(set(urls))
        content = self.parser.parse_html(urls=urls)
        content = [x for x in content if x]
        return content[:max_articles]