import string

from langchain_core.language_models import BaseChatModel
from nltk import sent_tokenize, FreqDist
import nltk
nltk.download("stopwords")
from nltk.corpus import stopwords

from ..query_master import SearchQueryToNSubquery,SearchRetriever,QueryRefiner

class AdvancedAISearcher:
    def __init__(self, chunk_overlap=25,
                 chunk_size=250,
                 max_urls=5,
                 n_key_sentences = 25,
                 topk = 10):
        self.n_key_sentences = n_key_sentences
        self.chunk_overlap = chunk_overlap
        self.chunk_size = chunk_size
        self.max_urls = max_urls
        self.topk = topk

    def generic_search(self, llm: BaseChatModel, query: str,
               verbose:bool = False,
               return_content_list = False,
                       n_splits = None)-> str:
        refined_query = QueryRefiner.refine_query(llm=llm, query=query)
        if verbose:
            print(f"Refined Query: {refined_query}")

        query_splits = SearchQueryToNSubquery.ai_splits(llm=llm, query=refined_query,
                                                        n_splits=n_splits)
        if verbose:
            print(f"Query Splits: {query_splits}")
        retriever = SearchRetriever(
            chunk_overlap=self.chunk_overlap,
            chunk_size=self.chunk_size,
            max_urls=self.max_urls,
        )
        ans = []
        all_urls = []
        for chunk in query_splits.get("refined_splits", []):
            results = retriever.query_based_content_retrieval(chunk,verbose=verbose,topk=self.topk)
            ans.extend(results.topk_chunks)
            all_urls.extend(results.urls)
        join_urls = "\n".join(all_urls)
        if return_content_list:
            return ans,all_urls
        ans = "\n".join(ans)
        final_ans = f"Answer:\n{ans}\n\nURLs:\n{join_urls}"
        return final_ans

    def search(self, llm: BaseChatModel, query: str,
               verbose:bool = False)-> str:
        refined_query = QueryRefiner.refine_query(llm=llm, query=query)
        if verbose:
            print(f"Refined Query: {refined_query}")

        query_splits = SearchQueryToNSubquery.ai_splits(llm=llm, query=refined_query)
        if verbose:
            print(f"Query Splits: {query_splits}")
        retriever = SearchRetriever(
            chunk_overlap=self.chunk_overlap,
            chunk_size=self.chunk_size,
            max_urls=self.max_urls,
        )
        ans = []
        all_urls = []
        for chunk in query_splits.get("refined_splits", []):
            results = retriever.query_based_content_retrieval(chunk,verbose=verbose)
            ans.extend(results.topk_chunks)
            all_urls.extend(results.urls)
        join_urls = "\n".join(all_urls)

        all_sentences = []
        for i, answer in enumerate(ans):
            all_sentences.extend(self.__preprocess_text(answer, i))
        key_sentences = self.__extract_key_sentences(all_sentences, n=self.n_key_sentences)

        context = "\n".join(list(set([i[1] for i in key_sentences])))
        final_ans = f"Answer:\n{context}\n\nURLs:\n{join_urls}"
        return final_ans

    def __preprocess_text(self,text, i):
        # Tokenize the text into sentences
        org_sentences = sent_tokenize(text)

        # Remove punctuation and convert to lowercase
        sentences = [s.translate(str.maketrans('', '', string.punctuation)).lower() for s in org_sentences]

        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        sentences = [' '.join([word for word in s.split() if word not in stop_words]) for s in sentences]
        sentences = [(i, os, s) for os, s in zip(org_sentences, sentences)]
        return sentences

    def __extract_key_sentences(self,sentences, n=3):
        # Combine all sentences
        all_words = ' '.join([_[1] for _ in sentences]).split()

        # Calculate word frequencies
        freq_dist = FreqDist(all_words)

        # Score sentences based on word frequencies
        sentence_scores = []
        for idx, org_sent, sentence in sentences:
            score = sum(freq_dist[word] for word in sentence.split())
            sentence_scores.append((idx, org_sent, sentence, score))

        # Sort sentences by score and return top n
        return [s for s in sorted(sentence_scores, key=lambda x: x[-1], reverse=True)[:n]]

    def generate_final_answer(self,llm, query,verbose = False,n_splits = None):
        # Preprocess and extract key information
        answers, urls = self.generic_search(llm, query, return_content_list=True,
                                   verbose=verbose,
                                            n_splits = n_splits)
        all_sentences = []
        for i, answer in enumerate(answers):
            all_sentences.extend(self.__preprocess_text(answer, i))
        key_sentences = self.__extract_key_sentences(all_sentences, n=self.n_key_sentences)

        context = "\n".join(list(set([i[1] for i in key_sentences])))
        prompt = f"""Based on the following key information:

    {context}

    Please provide a brief answer to the query: "{query}"
    Focus only on the most crucial points."""

        response = llm.invoke(prompt).content
        return response
