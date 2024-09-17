import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from wordllama import WordLlama
from pyopengenai.researcher_ai import RealTimeGoogleSearchProvider, UrlTextParser


def fetch_and_store_search_results(query,file_name_json):
    parser = UrlTextParser()
    searcher = RealTimeGoogleSearchProvider()
    urls = searcher.perform_search(query)
    contents = parser.parse_html(urls)
    with open(file_name_json, "w", encoding='utf-8') as f:
        json.dump(contents, f, indent=2)

def tokenize_text(text, chunk_size=100, chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )
    return text_splitter.split_text(text)

def query_based_content_retrieval(query, topk=10,return_urls = False):
    parser = UrlTextParser()
    searcher = RealTimeGoogleSearchProvider()
    urls = searcher.perform_search(query)
    contents = parser.parse_html(urls)
    contents = [x for x in contents if x]
    splits = []
    for x in contents:
        splits.extend(tokenize_text(x))
    splitter = WordLlama.load()
    tokens =  splitter.topk(query, splits, topk)
    if return_urls:
        return tokens,urls
    return tokens
