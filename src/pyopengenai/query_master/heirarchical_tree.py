import json
import re
from pathlib import Path
from collections import defaultdict
from typing import List

import numpy as np
from queue import PriorityQueue
from graphviz import Digraph
from wordllama import WordLlama
from wordllama.algorithms import kmeans_clustering


class HierarchicalSentenceTree:
    class Node:
        def __init__(self, embedding, text=None):
            self.embedding = embedding
            self.text = text
            self.children = []
            self.id = id(self)

        def __le__(self, other):
            return np.linalg.norm(self.embedding) <= np.linalg.norm(other.embedding)

        def __lt__(self, other):
            return np.linalg.norm(self.embedding) < np.linalg.norm(other.embedding)

    def __init__(
        self,
        text_or_chunks: str | List[str],
        max_depth=5,
        min_cluster_size=3,
        load_tree = True
    ):
        self.context = text_or_chunks
        self.max_depth = max_depth
        self.min_cluster_size = min_cluster_size
        self.root = None
        self.wl = WordLlama.load()
        self.load_tree = load_tree
        self.sentences = self._split_sentences()
        self._load_tree()

    def _split_sentences(self):
        if isinstance(self.context, str):
            findings: List = re.findall(r'[^!.?]+[!.?]',
                                        self.context)
        else:
            return self.context
        return findings

    def build_tree(self, sentences):
        embeddings = self.wl.embed(sentences, norm=True)
        self.root = self.Node(np.mean(embeddings, axis=0))
        queue = [(self.root, embeddings, sentences, 0)]

        while queue:
            node, node_embeddings, node_sentences, depth = queue.pop(0)

            if depth >= self.max_depth or len(node_embeddings) <= self.min_cluster_size:
                for emb, sent in zip(node_embeddings, node_sentences):
                    node.children.append(self.Node(emb, sent))
                continue

            k = max(2, min(int(len(node_embeddings) ** 0.5), 5))  # Limit max clusters to 5
            cluster_labels, _ = kmeans_clustering(
                node_embeddings,
                k=k,
                max_iterations=100,
                tolerance=1e-4,
                n_init=10,
                min_iterations=5,
                random_state=None
            )

            label_maps = defaultdict(list)
            for idx, val in enumerate(cluster_labels):
                label_maps[val].append(idx)

            for cluster_indices in label_maps.values():
                cluster_embeddings = node_embeddings[cluster_indices]
                cluster_sentences = [node_sentences[i] for i in cluster_indices]
                child_node = self.Node(np.mean(cluster_embeddings, axis=0))
                node.children.append(child_node)
                queue.append((child_node, cluster_embeddings, cluster_sentences, depth + 1))

    def visualize_tree(self, output_file='sentence_tree'):
        dot = Digraph(comment='Hierarchical Sentence Tree')
        dot.attr(rankdir='TB', size='40,40', dpi='300', fontname='Arial')

        def add_nodes(node, parent=None):
            if node.text:
                dot.node(str(node.id), node.text[:50] + '...' if len(node.text) > 50 else node.text,
                         shape='box', style='filled', fillcolor='lightblue',
                         fontsize='10', width='3', height='0.5')
            else:
                dot.node(str(node.id), f'Cluster\n{len(node.children)} items',
                         shape='ellipse', style='filled', fillcolor='lightgreen',
                         fontsize='12', width='1.5', height='1.5')

            if parent:
                dot.edge(str(parent.id), str(node.id))

            for child in node.children:
                add_nodes(child, node)

        add_nodes(self.root)

        dot.render(output_file, view=True, format='png', cleanup=True,
                   engine='dot', renderer='cairo', formatter='cairo')

    @staticmethod
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search_tree(self, query_embedding, k=5):
        results = []
        pq = PriorityQueue()
        pq.put((-self.cosine_similarity(query_embedding, self.root.embedding), self.root))

        while not pq.empty() and len(results) < k:
            _, node = pq.get()

            if node.text:  # Leaf node (sentence)
                results.append((node.text, self.cosine_similarity(query_embedding, node.embedding)))
            else:  # Internal node (cluster)
                for child in sorted(node.children,
                                    key=lambda x: self.cosine_similarity(query_embedding, x.embedding),
                                    reverse=True):
                    pq.put((-self.cosine_similarity(query_embedding, child.embedding), child))

        return results

    def _query(self, query, k=5):
        query_embedding = self.wl.embed([query], norm=True)[0]
        results = self.search_tree(query_embedding, k)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def top_k(self,query,k = 5):
        results = self._query(query, k)
        if results:
            results = [_[0] for _ in results]
        return results

    def top_k_with_scores(self,query,k = 5):
        return self._query(query,k)

    def topk_optimal(self, query):
        query_embedding = self.wl.embed([query], norm=True)[0]

        # Start with a large k
        initial_k = 50
        results = self.search_tree(query_embedding, k=initial_k)

        # Sort results by similarity score (highest to lowest)
        results.sort(key=lambda x: x[1], reverse=True)

        # Calculate the average similarity score
        avg_similarity = sum(score for _, score in results) / len(results)

        # Find the optimal cut-off point
        optimal_k = 1
        for i, (_, score) in enumerate(results):
            if score < avg_similarity:
                optimal_k = i
                break

        # Ensure we return at least one result, but no more than 10
        optimal_k = max(1, min(optimal_k, 10))

        return [text for text, _ in results[:optimal_k]]

    def _load_tree(self):
        if self.load_tree:
            self.build_tree(self.sentences)

# Example usage:
if __name__ == "__main__":
    # Load sentences
    text = Path("/home/ntlpt59/Downloads/combined_text.txt").read_text()
    print(len(text))
    # Create and build the tree
    tree = HierarchicalSentenceTree(text_or_chunks=text)

    # Visualize the tree
    # tree.visualize_tree()

    # Query the tree
    query = "how to call other functions using ollama?"
    top_k_results = tree.top_k(query,5)
    for x in top_k_results:
        print(x)
        print('#'*50)
