import re
from typing import List
import concurrent.futures
import torch
from wordllama import WordLlama

class WordLLamaRetriever:
    def __init__(self, text, batch_size=32):
        self.wl = WordLlama.load()
        self.text = text
        self.embeds = None
        self.sents = None
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.__build_embeds()

    @staticmethod
    def _split_sentences(text):
        return re.findall(r'[^!.?]+[!.?]', text) if isinstance(text, str) else text

    def embed_batch(self, sents_batch):
        with torch.no_grad():
            return torch.tensor(self.wl.embed(sents_batch)).to(self.device)

    def get_embeds(self, text) -> tuple:
        sents: List = self._split_sentences(text)
        embeds = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for i in range(0, len(sents), self.batch_size):
                sents_batch = sents[i:i + self.batch_size]
                futures.append(executor.submit(self.embed_batch, sents_batch))

            for future in concurrent.futures.as_completed(futures):
                embeds.append(future.result())

        if embeds:
            embeds = torch.cat(embeds, dim=0)
        else:
            embeds = None

        return embeds, sents

    def top_k(self, query, k=5):
        q_embeds, _ = self.get_embeds(query)

        if self.embeds is None or q_embeds is None:
            return []

        # Normalize query embeddings
        q_embeds = torch.nn.functional.normalize(q_embeds, p=2, dim=1)

        # Compute cosine similarity
        similarity = torch.mm(self.embeds, q_embeds.t())

        # Get top k similarities and indices
        top_k_similarities, top_k_indices = torch.topk(similarity.squeeze(), k)

        top_sents = [self.sents[i] for i in top_k_indices]
        return top_sents

    def __build_embeds(self):
        self.embeds, self.sents = self.get_embeds(self.text)
        if self.embeds is not None:
            # Normalize embeddings
            self.embeds = torch.nn.functional.normalize(self.embeds, p=2, dim=1)

if __name__ == '__main__':
    import time

    with open("/home/ntlpt59/Downloads/combined_text.txt", "r") as file:
        large_text = file.read()

    start_time = time.time()
    ht = WordLLamaRetriever(large_text)
    build_time = time.time() - start_time

    query_time = time.time()
    sents = ht.top_k("what is date of coo?")
    query_time = time.time() - query_time

    print(f"Build time: {build_time:.2f} seconds")
    print(f"Query time: {query_time:.2f} seconds")
