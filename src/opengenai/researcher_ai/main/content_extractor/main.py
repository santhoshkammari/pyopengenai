from ..semantic_chunker import SemanticSimilarityTextChunker


class ContextExtractor:
    def __init__(self, top_chunks_in_article=3, sentence_chunk_size_in_article=3, max_subquery_relevant_chunks=3):
        self.top_chunks_in_article = top_chunks_in_article
        self.sentence_chunk_size_in_article = sentence_chunk_size_in_article
        self.max_subquery_relevant_chunks = max_subquery_relevant_chunks

    def extract_context(self, query, articles):
        chunker = SemanticSimilarityTextChunker(query)
        all_chunks = []

        for article in articles:
            chunks = chunker.chunk_text(
                article,
                top_chunks_in_article=self.top_chunks_in_article,
                chunk_size=self.sentence_chunk_size_in_article
            )
            all_chunks.extend(chunks)

        all_chunks.sort(
            key=lambda chunk: chunker.score_sentence(chunk, chunker.get_query_keywords()),
            reverse=True
        )

        relevant_chunks = all_chunks[:self.max_subquery_relevant_chunks]
        return relevant_chunks

# Example usage:
# extractor = ContextExtractor(top_chunks_in_article=5, sentence_chunk_size_in_article=3, max_subquery_relevant_chunks=10)
# relevant_chunks = extractor.extract_context("example query", ["article1 text", "article2 text"])