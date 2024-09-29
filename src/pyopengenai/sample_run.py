from langchain_ollama import ChatOllama
from .ai_searcher import AdvancedAISearcher

from .query_master import SearchRetriever

def get_llm():
    llm = ChatOllama(model = "qwen2.5:1.5b-instruct",temperature = 0,num_predict=8_000)
    return llm
# query  = "explain me Design of ACM , better if we use arxiv paper"
def ai_search(query,verbose: bool|str= False,
              llm = None):
    if llm is None:
        llm = get_llm()
    rtr = AdvancedAISearcher()
    if isinstance(verbose,str): verbose = verbose.lower() == 'true'
    res = rtr.generate_final_answer(llm, query,verbose=verbose)
    return res

def search(query,verbose: bool|str = False,
           llm= None):
    if llm is None:
        llm = get_llm()
    rtr = AdvancedAISearcher()
    if isinstance(verbose,str): verbose = verbose.lower() == 'true'
    res = rtr.search(llm,query,verbose=verbose)
    return res

def fast_search(query,verbose: bool|str = False,
                llm= None):
    if llm is None:
        llm = get_llm()
    rtr = AdvancedAISearcher(chunk_overlap=20,
                             chunk_size=100,
                             max_urls=2,
                             n_key_sentences=10)
    if isinstance(verbose,str): verbose = verbose.lower() == 'true'
    res = rtr.search(llm,query,verbose=verbose)
    return res

def google_search(query,verbose: bool|str = False):
    retriever = SearchRetriever()
    if isinstance(verbose,str): verbose = verbose.lower() == 'true'
    results = retriever.query_based_content_retrieval(query, topk=5,verbose=verbose)
    return "\n".join(results.topk_chunks)


