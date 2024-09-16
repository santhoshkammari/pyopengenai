import json
import os
import logging
import networkx as nx
import matplotlib.pyplot as plt

from datetime import datetime
from typing import List
from .researcher import AiResearcher
from .semantic_chunker import SemanticSimilarityTextChunker
from .llm_service.base import LLMPrompt
from .prompts import Prompt

class MultiAgentQueryOrchestrator:
    def __init__(self,response_level="medium",device = "Local",model = None):
        self.device = device
        self.results = {}
        self.response_level = response_level
        self.results_folder = False
        self.researcher = AiResearcher()
        self.setup_logging()

        self.num_queries = 3
        self.model = model
        self.subquery_max_urls = 3
        self.subquery_max_articles = 3
        self.top_chunks_in_article = 3
        self.max_subquery_relevant_chunks = 5
        self.sentence_chunk_size_in_article = 3
        self.setup_args()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
        self.logger = logging.getLogger(__name__)

    def create_results_folder(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"Results/results_{timestamp}"
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def save_to_results(self, filename, content):
        if self.results_folder:
            full_path = os.path.join(self.results_folder, filename)
            with open(full_path, 'w') as f:
                if isinstance(content, str):
                    f.write(content)
                else:
                    json.dump(content, f, indent=2)
        else:
            file_name= filename.rsplit('.', 1)[0]
            self.results.update({file_name:content})
        self.logger.info(f"Saved {filename} to results folder")

    def decompose_query(self, query: str, num_queries: int) -> List[str]:
        self.logger.info(f"Decomposing query: {query}")
        decompose_prompt = LLMPrompt(Prompt.DECOMPOSE_PROMPT,model=self.model,
                                     device=self.device
                                     )
        subqueries_str = decompose_prompt.run(websearchquery=query,
                                              num_queries=num_queries,
                                              return_type=list)
        subqueries_str = subqueries_str.replace("'", '"')
        subqueries = json.loads(subqueries_str)
        self.save_to_results("subqueries.json", subqueries)
        return subqueries

    def visualize_dependency_graph(self, G: nx.DiGraph):
        self.logger.info("Visualizing dependency graph")
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue',
                node_size=2000, font_size=10, arrows=True)

        labels = nx.get_node_attributes(G, 'query')
        label_pos = {k: (v[0], v[1] + 0.02) for k, v in pos.items()}
        nx.draw_networkx_labels(G, label_pos, labels, font_size=8, font_weight="bold")

        edge_labels = {(u, v): "" for (u, v) in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

        plt.title("Subquery Dependency Graph")
        plt.axis('off')
        plt.tight_layout()
        filename = os.path.join(self.results_folder, "dependency_graph.png")
        plt.savefig(filename, format="png", dpi=300, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Graph visualization saved as {filename}")

    def create_dependency_graph(self, subqueries: List[str]) -> nx.DiGraph:
        self.logger.info("Creating dependency graph")
        G = nx.DiGraph()
        for i, sq in enumerate(subqueries):
            G.add_node(i, query=sq)

        for i in range(len(subqueries)):
            for j in range(i + 1, len(subqueries)):
                dependency_prompt = LLMPrompt(Prompt.NODE_DEPENDENCY_PROMPT,model=self.model,
                                              device=self.device
                                              )
                dependency = dependency_prompt.run(first=subqueries[i],
                                                   second=subqueries[j]).strip().lower()
                if 'yes' in dependency:
                    G.add_edge(j, i)

        return G

    def process_subquery(self, subquery: str, context: str = "") -> str:
        self.logger.info(f"Processing subquery: {subquery}")
        articles = self.researcher.get_query_content(subquery, max_articles=self.subquery_max_articles,
                                                     max_urls=self.subquery_max_urls)
        chunker = SemanticSimilarityTextChunker(subquery)
        all_chunks = []
        for article in articles:
            chunks = chunker.chunk_text(article,
                                        top_chunks_in_article=self.top_chunks_in_article,
                                        chunk_size=self.sentence_chunk_size_in_article)
            all_chunks.extend(chunks)
        all_chunks.sort(key=lambda chunk: chunker.score_sentence(chunk, chunker.get_query_keywords()), reverse=True)
        relevant_chunks = all_chunks[:self.max_subquery_relevant_chunks]  # Top 3 chunks

        combined_input = context + "\n\n" + "\n".join(relevant_chunks)
        answer_prompt = LLMPrompt(Prompt.ANSWER_PROMPT,model=self.model,
                                  device=self.device
                                  )
        return answer_prompt.run(combined_input=combined_input, subquery=subquery)

    def save_graph(self, G: nx.DiGraph):
        self.logger.info("Saving dependency graph")
        data = nx.node_link_data(G)
        self.save_to_results("dependency_graph.json", data)

    def load_graph(self) -> nx.DiGraph:
        self.logger.info("Loading dependency graph")
        filename = os.path.join(self.results_folder, "dependency_graph.json")
        with open(filename, 'r') as f:
            data = json.load(f)
        return nx.node_link_graph(data)

    def extract_relevant_info(self, subquery: str, web_result: str, child_context: str) -> str:
        self.logger.info(f"Extracting relevant info for subquery: {subquery}")
        runner = LLMPrompt(Prompt.RELEVANT_INFO_PROMPT,model=self.model,
                           device=self.device
                           )
        return runner.run(
            subquery=subquery,
            web_result=web_result,
            child_context=child_context
        )

    def process_query(self, query: str, num_queries=None) -> str:
        if num_queries is None:
            num_queries = self.num_queries
        self.logger.info(f"Processing main query: {query}")
        subqueries = self.decompose_query(query=query, num_queries=num_queries)
        self.logger.info(f"Subqueries\n {subqueries}")
        graph = self.create_dependency_graph(subqueries)
        if self.results_folder:
            self.visualize_dependency_graph(graph)
            self.save_graph(graph)

        results = {}
        for node in reversed(list(nx.topological_sort(graph))):
            results[node] = {}
            subquery = graph.nodes[node]['query']
            self.logger.info(f"Processing subquery: {subquery}")
            web_result = self.process_subquery(subquery)
            results[node]["web_result"] = web_result

            child_results = [results.get(child, {}).get("relevant_info", "") for child in graph.successors(node)]
            child_context = "\n".join(child_results)

            relevant_info = self.extract_relevant_info(subquery, web_result, child_context)
            results[node]["relevant_info"] = relevant_info

        self.save_to_results("subquery_results.json", results)

        final_context = "\n".join([f"Subquery {i + 1}: {subquery}\nResult: {results[i]['relevant_info']}\n"
                                   for i, subquery in enumerate(subqueries)])

        self.logger.info("Generating final answer")
        runner = LLMPrompt(Prompt.COMPREHENSIVE_ANSWER_PROMPT,model=self.model,
                           device=self.device
                           )
        final_answer = runner.run(
            final_context=final_context,
            query=query
        )
        self.save_to_results("final_answer.txt", final_answer)
        return final_answer

    def setup_args(self):
        if self.results_folder:
            self.results_folder = self.create_results_folder()

        if self.response_level=="low":
            self.num_queries=3
            self.model = "qwen2:1.5b-instruct" if self.model is None else self.model
            self.subquery_max_urls = 2
            self.subquery_max_articles = 2
            self.top_chunks_in_article = 2
            self.max_subquery_relevant_chunks = 2
            self.sentence_chunk_size_in_article = 2
        elif self.response_level=="high":
            self.num_queries=8
            self.model = "qwen2:7b-instruct" if self.model is None else self.model
            self.subquery_max_urls = 4
            self.subquery_max_articles = 4
            self.top_chunks_in_article = 4
            self.max_subquery_relevant_chunks = 5
            self.sentence_chunk_size_in_article = 3
        else:
            self.num_queries=5
            self.model = "qwen2:7b-instruct" if self.model is None else self.model
            self.subquery_max_urls = 3
            self.subquery_max_articles = 3
            self.top_chunks_in_article = 3
            self.max_subquery_relevant_chunks = 5
            self.sentence_chunk_size_in_article = 3


if __name__ == '__main__':
    processor = MultiAgentQueryOrchestrator(
            response_level="low",
            device="GPU"
        )
    query = "when is pawan kalyan new movie OG release date?"
    result = processor.process_query(query)
    print(processor.results)