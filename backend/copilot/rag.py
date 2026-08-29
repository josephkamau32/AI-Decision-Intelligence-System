from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from typing import List, Dict, Any
import pandas as pd
from ..ml.data_ingestion import DataIngestion, DataProfiler
from ..services.dataset_service import dataset_service
from ..services.model_service import model_service
from ..utils.config import settings

class RAGSystem:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vectorstore = Chroma(
            collection_name="dataset_insights",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    def index_dataset(self, dataset_id: str):
        """Index dataset schema, statistics, and insights."""
        dataset = next((d for d in dataset_service.datasets if d.id == dataset_id), None)
        if not dataset:
            return

        df = DataIngestion.load_data(dataset.file_path)
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        # Create documents
        documents = []

        # Schema document
        schema_text = f"Dataset: {dataset.name}\nColumns: {', '.join(profile['columns'])}\nData Types: {profile['column_types']}\nShape: {profile['shape']}"
        documents.append(Document(page_content=schema_text, metadata={"type": "schema", "dataset_id": dataset_id}))

        # Statistics document
        stats_text = f"Missing Values: {profile['missing_values']}\nOutliers: {profile['outliers']}\nTarget Variable: {profile['target_variable']}\nProblem Type: {profile['problem_type']}"
        documents.append(Document(page_content=stats_text, metadata={"type": "statistics", "dataset_id": dataset_id}))

        # Split and add to vectorstore
        docs = self.text_splitter.split_documents(documents)
        self.vectorstore.add_documents(docs)

    def index_model_insights(self, model_id: str):
        """Index model insights like feature importance."""
        model = model_service.models.get(model_id)
        if not model:
            return

        # Assuming model has feature_importances_ for tree-based models
        if hasattr(model, 'feature_importances_'):
            # Need to get feature names from dataset
            # For simplicity, assume we can get from recent dataset
            dataset = dataset_service.datasets[-1] if dataset_service.datasets else None
            if dataset:
                df = DataIngestion.load_data(dataset.file_path)
                features = list(df.columns[:-1])  # Assume last is target
                importance_text = "\n".join([f"{feat}: {imp:.4f}" for feat, imp in zip(features, model.feature_importances_)])
                doc = Document(page_content=f"Feature Importance for model {model_id}:\n{importance_text}", metadata={"type": "feature_importance", "model_id": model_id})
                docs = self.text_splitter.split_documents([doc])
                self.vectorstore.add_documents(docs)

    def retrieve_relevant_info(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve relevant documents for a query."""
        return self.vectorstore.similarity_search(query, k=k)

    def get_context(self, query: str) -> str:
        """Get context string from retrieved documents."""
        docs = self.retrieve_relevant_info(query)
        return "\n\n".join([doc.page_content for doc in docs])

rag_system = RAGSystem()