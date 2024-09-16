
import json

import spacy
import numpy as np
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

class SemanticSimilarityTextChunker:
    def __init__(self, query):
        self.query = query
        self.nlp = spacy.load("en_core_web_sm")
        self.stop_words = set(stopwords.words('english'))

    def preprocess_text(self, text):
        doc = self.nlp(text.lower())
        return [token.lemma_ for token in doc if token.text not in self.stop_words and token.is_alpha]

    def get_query_keywords(self):
        return self.preprocess_text(self.query)

    def calculate_similarity(self, word1, word2):
        return word1.similarity(word2)

    def score_sentence(self, sentence, keywords):
        preprocessed_sentence = self.preprocess_text(sentence)
        doc_sentence = self.nlp(" ".join(preprocessed_sentence))
        doc_keywords = self.nlp(" ".join(keywords))

        if not doc_sentence.vector.any() or not doc_keywords.vector.any():
            return 0

        # Calculate the average similarity between each word in the sentence and the keywords
        similarities = []
        for token in doc_sentence:
            if token.has_vector:
                keyword_similarities = [self.calculate_similarity(token, keyword) for keyword in doc_keywords if
                                        keyword.has_vector]
                if keyword_similarities:
                    similarities.append(max(keyword_similarities))

        # Calculate the average similarity score
        avg_similarity = np.mean(similarities) if similarities else 0

        # Adjust the score based on the presence of exact matches
        exact_match_bonus = sum(1 for word in preprocessed_sentence if word in keywords)
        adjusted_score = (avg_similarity + 0.1 * exact_match_bonus) / (1 + 0.1 * len(keywords))

        return adjusted_score

    def chunk_text(self, text, chunk_size=3,top_chunks_in_article=3):
        sentences = sent_tokenize(text)
        keywords = self.get_query_keywords()

        # Score each sentence
        scored_sentences = [(sentence, self.score_sentence(sentence, keywords)) for sentence in sentences]

        # Sort sentences by score in descending order
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Group top-scoring sentences into chunks
        chunks = []
        for i in range(0, min(len(scored_sentences), chunk_size * 3), chunk_size):
            chunk = ' '.join([sent[0] for sent in scored_sentences[i:i + chunk_size]])
            chunks.append(chunk)

        return chunks[:top_chunks_in_article]  # Return top 3 chunks