import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from typing import List, Dict, Any

class KnowledgeBase:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="hvac_knowledge",
            embedding_function=self.embedding_fn
        )

    def ingest_pdf(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF path {pdf_path} does not exist. Skipping ingestion.")
            return

        reader = PdfReader(pdf_path)
        documents = []
        metadatas = []
        ids = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                documents.append(text)
                metadatas.append({"page": i + 1, "source": os.path.basename(pdf_path)})
                ids.append(f"page_{i + 1}")

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Ingested {len(documents)} pages from {pdf_path}")

    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

if __name__ == "__main__":
    kb = KnowledgeBase()
    # Attempt to ingest the specified PDF
    kb.ingest_pdf("/home/team/shared/Ultimate_HVAC_Knowledge_Fortress.pdf")
    # Also check other potential locations
    kb.ingest_pdf("./Ultimate_HVAC_Knowledge_Fortress.pdf")
