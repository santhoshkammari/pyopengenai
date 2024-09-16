import asyncio
import os
from functools import lru_cache

import aiohttp
import trafilatura
from bs4 import BeautifulSoup

from nltk.tokenize import sent_tokenize
from transformers import pipeline
import re

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from .text_filter import TextFilter



class FastHTMLParser:
    def __init__(self, urls,fast_response = False):
        self.urls = urls
        self.fast_response = fast_response

    async def _fetch_url(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return trafilatura.extract(html) or ""
                else:
                    return ""
        except Exception:
            return ""

    async def __fetch_all_urls(self):
        async with aiohttp.ClientSession() as session:
            if self.fast_response:
                for url in self.urls:
                    result = await self._fetch_url(session, url)
                    if result:
                        return [result]
                return []
            else:
                tasks = [self._fetch_url(session, url) for url in self.urls]
                return await asyncio.gather(*tasks)
    def fetch_content(self):
        return asyncio.run(self.__fetch_all_urls())


class FastHTMLParserV2:
    def __init__(self, urls, fast_response=False, max_length=1000, summarize=False):
        self.urls = urls
        self.fast_response = fast_response
        self.max_length = max_length
        self.summarize = summarize
        if summarize:
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    async def _fetch_url(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._process_html(html)
                else:
                    return ""
        except Exception as e:
            # print(f"Error fetching {url}: {str(e)}")
            return ""

    def _process_html(self, html):
        # Extract main content using trafilatura
        extracted_text = trafilatura.extract(html) or ""

        # Use BeautifulSoup for additional cleaning
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, and nav elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Combine trafilatura and BeautifulSoup results
        combined_text = f"{extracted_text}\n\n{text}"

        # Remove extra whitespace and newlines
        cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()

        # Split into sentences
        sentences = sent_tokenize(cleaned_text)

        # Truncate if necessary
        if len(sentences) > self.max_length:
            sentences = sentences[:self.max_length]

        # Join sentences with newlines for better formatting
        formatted_text = '\n'.join(sentences)

        if self.summarize:
            return self._summarize_text(formatted_text)
        else:
            return formatted_text

    def _summarize_text(self, text):
        # Split text into chunks of 1000 tokens (approximate)
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
        summaries = []
        for chunk in chunks:
            summary = self.summarizer(chunk, max_length=100, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        return ' '.join(summaries)

    async def __fetch_all_urls(self):
        async with aiohttp.ClientSession() as session:
            if self.fast_response:
                for url in self.urls:
                    result = await self._fetch_url(session, url)
                    if result:
                        return [result]
                return []
            else:
                tasks = [self._fetch_url(session, url) for url in self.urls]
                return await asyncio.gather(*tasks)

    def fetch_content(self):
        return asyncio.run(self.__fetch_all_urls())

class FastHTMLParserV3:
    def __init__(self, urls, fast_response=False, max_length=None, summarize=False, summary_sentences=3):
        self.urls = urls
        self.fast_response = fast_response
        self.max_length = max_length
        self.summarize = summarize
        self.summary_sentences = summary_sentences
        if summarize:
            self.summarizer = LsaSummarizer(Stemmer('english'))
            self.summarizer.stop_words = get_stop_words('english')

    @lru_cache
    async def _fetch_url(self, session, url, url_fetch_timeout=10):
        if self._is_avoid_urls(url):
            return ""
        try:
            async with session.get(url, timeout=url_fetch_timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    # return self._process_html(html)
                    return self._process_trafili_html(html)
                else:
                    # print(f"Error fetching {url}: HTTP status {response.status}")
                    return ""
        except aiohttp.ClientConnectorError as e:
            print(f"Connection error for {url}: {str(e)}")
            return ""
        except asyncio.TimeoutError:
            print(f"Timeout error for {url}")
            return ""
        except Exception as e:
            print(f"Unexpected error fetching {url}: {str(e)}")
            return ""

    def _process_html(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\[.*?\]', '', text)
            if self.max_length is None:
                self.max_length = len(text)

            if len(text) > self.max_length:
                text = text[:self.max_length]
            if self.summarize:
                return self._summarize_text(text)
            else:
                return text
        except Exception as e:
            print(f"Error processing HTML: {str(e)}")
            return ""

    def _summarize_text(self, text):
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summary = self.summarizer(parser.document, self.summary_sentences)
            return ' '.join(str(sentence) for sentence in summary)
        except Exception as e:
            print(f"Error summarizing text: {str(e)}")
            return text

    async def fetch_content(self,url_fetch_timeout=10):
        async with aiohttp.ClientSession() as session:
            if self.fast_response:
                for url in self.urls:
                    result = await self._fetch_url(session, url,url_fetch_timeout)
                    if result:
                        return [result]
                return []
            else:
                tasks = [self._fetch_url(session, url,url_fetch_timeout) for url in self.urls]
                return await asyncio.gather(*tasks)
                # return [result for result in await asyncio.gather(*tasks) if result]


    def _is_avoid_urls(self,url):
        if "https://arxiv.org/pdf" in url.lower() or url.endswith(".pdf") or "youtube.com/watch" in url.lower():
            return True
        return False

    def _process_trafili_html(self, html):
        text = trafilatura.extract(html, include_formatting=True)
        text = TextFilter.filter_text(text)
        return text

#
# class FastHTMLParserV3:
#     def __init__(self, urls, fast_response=False, max_length=1000, summarize=False, summary_sentences=3):
#         self.urls = urls
#         self.fast_response = fast_response
#         self.max_length = max_length
#         self.summarize = summarize
#         self.summary_sentences = summary_sentences
#         if summarize:
#             self.summarizer = LsaSummarizer(Stemmer('english'))
#             self.summarizer.stop_words = get_stop_words('english')
#
#     async def _fetch_url(self, session, url):
#         try:
#             async with session.get(url, timeout=10) as response:
#                 if response.status == 200:
#                     html = await response.text()
#                     return self._process_html(html)
#                 else:
#                     return ""
#         except Exception as e:
#             print(f"Error fetching {url}: {str(e)}")
#             return ""
#
#     def _process_html(self, html):
#         # Use BeautifulSoup for content extraction and cleaning
#         soup = BeautifulSoup(html, 'lxml')
#
#         # Remove unwanted elements
#         for element in soup(['script', 'style', 'nav', 'footer', 'header']):
#             element.decompose()
#
#         # Extract text
#         text = soup.get_text(separator=' ', strip=True)
#
#         # Clean text
#         text = re.sub(r'\s+', ' ', text)
#         text = re.sub(r'\[.*?\]', '', text)  # Remove content in square brackets
#
#         # Truncate if necessary
#         if len(text) > self.max_length:
#             text = text[:self.max_length]
#
#         if self.summarize:
#             return self._summarize_text(text)
#         else:
#             return text
#
#     def _summarize_text(self, text):
#         parser = PlaintextParser.from_string(text, Tokenizer("english"))
#         summary = self.summarizer(parser.document, self.summary_sentences)
#         return ' '.join(str(sentence) for sentence in summary)
#
#     async def __fetch_all_urls(self):
#         async with aiohttp.ClientSession() as session:
#             if self.fast_response:
#                 for url in self.urls:
#                     result = await self._fetch_url(session, url)
#                     if result:
#                         return [result]
#                 return []
#             else:
#                 tasks = [self._fetch_url(session, url) for url in self.urls]
#                 return await asyncio.gather(*tasks)
#
#     async def fetch_content(self):
#         return await self.__fetch_all_urls()