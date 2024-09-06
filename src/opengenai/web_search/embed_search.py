from fastembed import TextEmbedding
import numpy as np
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

from fastembed import TextEmbedding
import numpy as np
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


def fast_embedding_search(text_corpus: str, query: str, top_k: int = 5, top_tfidf=10,
                          chunk_size=500, chunk_overlap=50) -> List[Tuple[str, float]]:
    global embedding_model, tfidf_vectorizer

    # Initialize models (only once)
    if 'embedding_model' not in globals():
        embedding_model = TextEmbedding()
    if 'tfidf_vectorizer' not in globals():
        tfidf_vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    # Split the corpus into sentences
    sentences = text_splitter.split_text(text_corpus)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    # TF-IDF vectorization for initial filtering
    tfidf_matrix = tfidf_vectorizer.fit_transform(sentences)
    query_tfidf = tfidf_vectorizer.transform([query])

    # Calculate TF-IDF similarities
    tfidf_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()

    # Select top 2*top_k candidates based on TF-IDF similarity
    candidate_indices = np.argsort(tfidf_similarities)[-top_tfidf * top_k:][::-1]
    candidate_sentences = [sentences[i] for i in candidate_indices]

    # Batch encode the candidate sentences and query
    candidate_embeddings = np.array(list(embedding_model.embed(candidate_sentences)))
    query_embedding = np.array(list(embedding_model.embed([query])))[0]

    # Normalize embeddings for faster cosine similarity computation
    candidate_embeddings = normalize(candidate_embeddings)
    query_embedding = normalize(query_embedding.reshape(1, -1))

    # Compute cosine similarities
    cosine_scores = cosine_similarity(query_embedding, candidate_embeddings).flatten()

    # Get the top-k results
    top_indices = np.argsort(cosine_scores)[-top_k:][::-1]
    top_results = [(candidate_sentences[i], cosine_scores[i]) for i in top_indices]

    return top_results


def fast_embed_backup(text_corpus: str, query: str, top_k: int = 1) -> List[Tuple[str, float]]:
    # Initialize the TextEmbedding model
    embedding_model = TextEmbedding()

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    # Split the corpus into sentences
    sentences = text_splitter.split_text(text_corpus)

    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    # Encode the sentences and the query
    sentence_embeddings = list(embedding_model.embed(sentences))
    query_embedding = list(embedding_model.embed([query]))[0]

    # Convert to numpy arrays for efficient computation
    sentence_embeddings = np.array(sentence_embeddings)
    query_embedding = np.array(query_embedding)

    # Compute cosine similarities
    cosine_scores = np.dot(sentence_embeddings, query_embedding) / (
            np.linalg.norm(sentence_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Get the top-k results
    top_results = sorted(zip(sentences, cosine_scores), key=lambda x: x[1], reverse=True)[:top_k]

    return top_results