import logging

from .parse_url.html_parser import UrlTextParser
from .search_provider.searcher import RealTimeGoogleSearchProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AiResearcher:
    def __init__(self, search_provider = 'google'):
        self.searcher = RealTimeGoogleSearchProvider(search_provider=search_provider)
        self.parser = UrlTextParser()

    def get_query_content(self,query,max_articles = 3,max_urls=6,return_urls=False):
        """
        Gets the top 3 URLs for the given query, fetches their content,
        returns the first three contents.'
        """
        urls = self.searcher.perform_search(query,
                                       max_urls=max_urls)
        urls = list(set(urls))
        logger.info(f"URls found: {urls}")
        content = self.parser.parse_html(urls=urls)
        content = [x for x in content if x]
        if return_urls:
            return content[:max_articles],urls
        return content[:max_articles]