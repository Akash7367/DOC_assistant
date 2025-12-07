import os
import faiss
import numpy as np
from typing import List
from langchain.schema import Document

INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'index.faiss')
DIM = 384  # embedding dimension for all-MiniLM-L6-v2

class Retriever:
    def __init__(self):
        self.index = None
        self.metadatas = []
        self.embeddings = None
        self._load()

    def _load(self):
        if os.path.exists(INDEX_PATH):
            try:
                self.index = faiss.read_index(INDEX_PATH)
            except Exception:
                self.index = faiss.IndexFlatL2(DIM)
        else:
            self.index = faiss.IndexFlatL2(DIM)

    def add_documents(self, docs: List[Document], embeddings: List[List[float]]):
        arr = np.array(embeddings).astype('float32')
        self.index.add(arr)

        for d in docs:
            self.metadatas.append({
                'source': d.metadata.get('source'),
                'pos': d.metadata.get('pos'),
                'text': d.page_content
            })

        faiss.write_index(self.index, INDEX_PATH)

    def similarity_search(self, query: str, k: int = 4):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        q_emb = model.encode(query).astype('float32')

        if self.index.ntotal == 0:
            return []

        D, I = self.index.search(np.array([q_emb]), k)
        results = []

        for idx in I[0]:
            if idx < len(self.metadatas):
                meta = self.metadatas[idx]
                results.append(
                    Document(page_content=meta['text'], metadata={'source': meta['source']})
                )

        return results
