import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from urllib.parse import quote_plus

from nodriver.cdp.dom import query_selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import time
class SearchResult(BaseModel):
    query: str
    title_and_links: list = []
    urls: list = []
    search_provider: str  = ""

class OptimizedMultiQuerySearcher:
    def __init__(self, chromedriver_path="/usr/local/bin/chromedriver", max_workers=None,
                 animation = False):
        self.chromedriver_path = chromedriver_path
        self.max_workers = max_workers or min(32, cpu_count() -2)
        self.animation = animation
        self.driver_pool = []
        self.params = {
            "bing":{"search":"b_results","find_element":".b_algo","head_selector":"h2"},
            "google": {"search": "search", "find_element": "div.g", "head_selector": "h3"}
        }

    def _setup_driver(self):
        chrome_options = Options()
        if not self.animation:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--start-maximized")
        chrome_options.page_load_strategy = 'none'
        return webdriver.Chrome(self.chromedriver_path, options=chrome_options)

    def _get_driver(self):
        if not self.driver_pool:
            return self._setup_driver()
        return self.driver_pool.pop()

    def _return_driver(self, driver):
        self.driver_pool.append(driver)

    def cleanup(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def search_single_query(self, query, num_results=10,
                            search_provider="google"
                            ):
        driver = self._get_driver()
        try:
            encoded_query = quote_plus(query)
            search_url = f"https://www.{search_provider}.com/search?q={encoded_query}"
            driver.get(search_url)

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, self.params[search_provider]["search"]))
            )
            urls,search_results = self.javascript_based(search_provider=search_provider,
                                          num_results=num_results,
                                         driver = driver
                                         )

            return SearchResult(
                query=query,
                title_and_links=search_results,
                urls=urls,
                search_provider = search_provider
            )
        except Exception as e:
            logger.error(f"An error occurred while searching '{query}': {str(e)}")
            return SearchResult(query=query)
        finally:
            self._return_driver(driver)

    async def search_multiple_queries(self, queries: List[str], num_results=10,
                                      search_provider=None,return_only_urls = False
                                      ) -> List[SearchResult]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            providers_list = self.params.keys() if search_provider is None else [search_provider]
            tasks= [
                loop.run_in_executor(
                    executor,
                    self.search_single_query,
                    query,
                    num_results,
                    provider
                )
                for query in queries for provider in providers_list
            ]
            result = await asyncio.gather(*tasks)
            if return_only_urls:
                all_urls = [url.urls for url in result]
                filtered_urls = [y for x in zip(*all_urls) for y in x]
                return filtered_urls
            return result

    def __del__(self):
        for driver in self.driver_pool:
            driver.quit()

    def javascript_based(self, driver=None, search_provider=None, num_results=None):
        script = """
                                var results = [];
                                var elements = document.querySelectorAll('##find_element##');
                                for (var i = 0; i < arguments[0] && i < elements.length; i++) {
                                    var element = elements[i];
                                    var titleElement = element.querySelector('##head_selector##');
                                    var linkElement = element.querySelector('a');
                                    if (titleElement && linkElement) {
                                        results.push({
                                            title: titleElement.innerText,
                                            link: linkElement.href
                                        });
                                    }
                                }
                                return results;
                                """
        script = script.replace("##find_element##", self.params[search_provider]["find_element"])
        script = script.replace("##head_selector##", self.params[search_provider]["head_selector"])
        search_results = driver.execute_script(script, num_results)
        urls = [x['link'] for x in search_results if len(x['link']) > 0]
        return urls,search_results


if __name__ == '__main__':
    import time

    async def main():
        start_time = time.perf_counter()
        gs = OptimizedMultiQuerySearcher()
        # queries = ["who is narendra modi?", "what is python programming?", "latest news in technology"]
        queries=['Latest advancements in agentbased RAG models',
                  'RAG based approaches for autonomous agents recent research and applications',
                  'Comparative analysis of current agentbased RAG systems for specific application domain',
                  'Exploring the future of agentbased language understanding with RAG',
                  'OpenAIs AGI Evaluating its potential within a RAG framework'
                 ]

        results = await gs.search_multiple_queries(queries,search_provider="bing")
        end_time = time.perf_counter()
        for result in results:
            print(f"Query: {result.query}")
            print(f"Number of results: {len(result.title_and_links)}")
            print("---")
        print(f"Total time taken : {end_time-start_time}s")
        print(results)

    asyncio.run(main())