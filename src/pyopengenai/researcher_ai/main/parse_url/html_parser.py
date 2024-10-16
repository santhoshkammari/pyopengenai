import asyncio
from dataclasses import dataclass
import aiohttp
from io import BytesIO
import PyPDF2
from tqdm import tqdm
from ....web_search import FastHTMLParserV3

from .base import BaseHtmlParser


@dataclass
class UrlTextParser(BaseHtmlParser):
    def __init__(self,extract_pdf=True):
        self.extract_pdf = extract_pdf
    def parse_single_html(self,url:str):
        res = self.parse_html([url])
        if res:
            return res[0]
        return ""
    def parse_html(self, urls: list) -> list:
        return asyncio.run(self._async_html_parser(urls))

    async def _async_html_parser(self, urls):
        html_urls = []
        pdf_urls = []
        for url in tqdm(urls,desc = "processing urls",unit = 'url'):
            url = self._arxiv_url_fix(url)
            if '/pdf' in url or url.lower().endswith('.pdf'):
                pdf_urls.append(url)
            else:
                html_urls.append(url)

        results = []

        if html_urls:
            fetcher = FastHTMLParserV3(urls=html_urls)
            html_results = await fetcher.fetch_content()
            results.extend(html_results)

        if pdf_urls and self.extract_pdf:
            pdf_results = await self._fetch_pdf_content(pdf_urls)
            results.extend(pdf_results)

        return results

    async def _fetch_pdf_content(self, pdf_urls):
        async def fetch_pdf(session, url):
            async with session.get(url) as response:
                if response.status == 200:
                    pdf_content = await response.read()
                    pdf_file = BytesIO(pdf_content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
                else:
                    return ""

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_pdf(session, url) for url in pdf_urls]
            results = await asyncio.gather(*tasks)
            return results

    def _arxiv_url_fix(self, url):
        if 'https://arxiv.org/abs/' in url and self.extract_pdf:
            return url.replace('https://arxiv.org/abs/', 'https://arxiv.org/pdf/')
        elif 'http://arxiv.org/html/' in url:
            if self.extract_pdf:
                return url.replace('http://arxiv.org/html/', 'https://arxiv.org/pdf/')
            else:
                return url.replace('http://arxiv.org/html/', 'https://arxiv.org/abs/')
        else:
            return url


