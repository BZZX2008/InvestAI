import chromadb
from chromadb.config import Settings
from loguru import logger
import hashlib


class ChromaManager:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="investment_news"
        )

    def store_news_embeddings(self, news_items: list):
        """存储新闻向量嵌入"""
        documents = []
        metadatas = []
        ids = []

        for item in news_items:
            content = f"{item['title']} {item['content']}"
            doc_id = hashlib.md5(content.encode()).hexdigest()

            documents.append(content)
            metadatas.append({
                "source": item.get("source", ""),
                "timestamp": item.get("timestamp", ""),
                "category": item.get("category", ""),
                "impact_level": item.get("impact_level", "unknown")
            })
            ids.append(doc_id)

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Stored {len(news_items)} news items in vector DB")

    def search_similar_news(self, query: str, n_results: int = 5):
        """搜索相似新闻"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results