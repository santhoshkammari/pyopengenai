from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextProcessor:
    @staticmethod
    def tokenize_text(text, chunk_size=100, chunk_overlap=20):
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        return text_splitter.split_text(text)

    @staticmethod
    def tokenize_list(content: List | None = None,
                       chunk_size: int = 100,
                       chunk_overlap: int = 20
                       ):
        contents = [x for x in content if x]
        splits = []
        for x in contents:
            splits.extend(TextProcessor.tokenize_text(x,chunk_overlap=chunk_overlap,chunk_size=chunk_size))
        return splits


