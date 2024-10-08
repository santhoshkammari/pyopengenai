import PyPDF2
from wordllama import WordLlama
import tiktoken
import re


class PDFContentExtractor:
    def __init__(self, pdf_path, chunk_size=1000):
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.wl = WordLlama.load()
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.content = self._extract_pdf_content()
        self.chunks = self._create_chunks()

    def _extract_pdf_content(self):
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page in reader.pages:
                content += page.extract_text()
        return re.sub(r'\s+', ' ', content).strip()

    def _create_chunks(self):
        tokens = self.enc.encode(self.content)
        chunks = []
        for i in range(0, len(tokens), self.chunk_size):
            chunk = self.enc.decode(tokens[i:i + self.chunk_size])
            chunks.append(chunk)
        return chunks

    def get_relevant_content(self, query, top_k=5):
        ranked_chunks = self.wl.rank(query, self.chunks)
        return [chunk for chunk, score in ranked_chunks[:top_k]]

    def search(self, query, top_k=5):
        relevant_chunks = self.get_relevant_content(query, top_k)
        for i, chunk in enumerate(relevant_chunks, 1):
            print(f"\nChunk {i}:")
            print(chunk)
            print("-" * 50)


# Example usage
if __name__ == "__main__":
    pdf_path = "path/to/your/pdf/file.pdf"
    extractor = PDFContentExtractor(pdf_path)

    query = "Example query about a specific topic"
    extractor.search(query)