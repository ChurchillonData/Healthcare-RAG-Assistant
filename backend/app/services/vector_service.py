"""
Vector Database Service for Medical Document Retrieval
Handles embedding generation and similarity search for medical literature
"""

import numpy as np
import json
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, data_dir: str = "data/medical_docs"):
        """Initialize vector service for medical document retrieval"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Simple in-memory vector store for demo
        # In production, use proper vector databases like Pinecone, Weaviate, or Chroma
        self.documents = []
        self.embeddings = []
        self.document_metadata = []
        
        # Load existing data
        self._load_data()
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a medical document to the vector store
        
        Args:
            content: Document content
            metadata: Document metadata (title, authors, doi, etc.)
            
        Returns:
            Document ID
        """
        doc_id = f"doc_{len(self.documents)}"
        
        # Generate simple embedding (in production, use OpenAI embeddings or similar)
        embedding = self._generate_simple_embedding(content)
        
        self.documents.append(content)
        self.embeddings.append(embedding)
        self.document_metadata.append(metadata or {})
        
        # Save to disk
        await self._save_data()
        
        logger.info(f"Added document {doc_id} to vector store")
        return doc_id
    
    async def search_similar_documents(
        self, 
        query: str, 
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar medical documents
        
        Args:
            query: Search query
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar documents with metadata
        """
        if not self.documents:
            return []
        
        # Generate query embedding
        query_embedding = self._generate_simple_embedding(query)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and return top_k
        results = []
        for doc_idx, similarity in similarities:
            if similarity >= threshold and len(results) < top_k:
                results.append({
                    "content": self.documents[doc_idx],
                    "metadata": self.document_metadata[doc_idx],
                    "similarity": similarity,
                    "doc_id": f"doc_{doc_idx}"
                })
        
        return results
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """
        Generate a simple embedding for demo purposes
        In production, use OpenAI embeddings or other proper embedding models
        """
        # Simple bag-of-words embedding
        words = text.lower().split()
        word_count = {}
        
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Create a fixed-size embedding vector
        embedding_size = 100
        embedding = [0.0] * embedding_size
        
        # Hash words to embedding positions
        for word, count in word_count.items():
            hash_val = hash(word) % embedding_size
            embedding[hash_val] += count
        
        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a**2 for a in vec1) ** 0.5
        norm2 = sum(b**2 for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _save_data(self):
        """Save vector data to disk"""
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "metadata": self.document_metadata
        }
        
        file_path = self.data_dir / "vector_data.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    def _load_data(self):
        """Load vector data from disk"""
        file_path = self.data_dir / "vector_data.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.embeddings = data.get("embeddings", [])
                    self.document_metadata = data.get("metadata", [])
                logger.info(f"Loaded {len(self.documents)} documents from vector store")
            except Exception as e:
                logger.error(f"Error loading vector data: {e}")
    
    async def add_sample_medical_documents(self):
        """Add sample medical documents for demonstration"""
        
        sample_docs = [
            {
                "content": "Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels. Type 1 diabetes is an autoimmune condition where the pancreas produces little to no insulin. Type 2 diabetes is characterized by insulin resistance and relative insulin deficiency. Common symptoms include increased thirst, frequent urination, unexplained weight loss, fatigue, and blurred vision. Management includes blood glucose monitoring, medication, diet modification, and regular exercise.",
                "metadata": {
                    "title": "Diabetes Overview",
                    "source": "Medical Encyclopedia",
                    "category": "Endocrinology",
                    "keywords": ["diabetes", "glucose", "insulin", "symptoms"]
                }
            },
            {
                "content": "Hypertension, or high blood pressure, is a condition where the force of blood against artery walls is consistently too high. Normal blood pressure is less than 120/80 mmHg. Hypertension increases the risk of heart disease, stroke, and kidney problems. Risk factors include age, family history, obesity, physical inactivity, tobacco use, and excessive alcohol consumption. Treatment includes lifestyle modifications and antihypertensive medications.",
                "metadata": {
                    "title": "Hypertension Management",
                    "source": "Cardiology Guidelines",
                    "category": "Cardiology",
                    "keywords": ["hypertension", "blood pressure", "cardiovascular"]
                }
            },
            {
                "content": "COVID-19 is caused by the SARS-CoV-2 virus and primarily spreads through respiratory droplets. Common symptoms include fever, cough, shortness of breath, fatigue, and loss of taste or smell. Severe cases can lead to pneumonia, acute respiratory distress syndrome, and multi-organ failure. Prevention measures include vaccination, wearing masks, social distancing, and hand hygiene. Treatment depends on severity and may include supportive care, antiviral medications, and monoclonal antibodies.",
                "metadata": {
                    "title": "COVID-19 Clinical Overview",
                    "source": "CDC Guidelines",
                    "category": "Infectious Diseases",
                    "keywords": ["covid-19", "sars-cov-2", "respiratory", "pandemic"]
                }
            },
            {
                "content": "Cancer is a group of diseases characterized by uncontrolled cell growth and spread. It can develop in any part of the body. Common types include breast, lung, prostate, and colorectal cancer. Risk factors vary by cancer type but may include genetics, environmental exposures, lifestyle factors, and age. Early detection through screening programs improves outcomes. Treatment options include surgery, chemotherapy, radiation therapy, immunotherapy, and targeted therapy.",
                "metadata": {
                    "title": "Cancer Overview and Treatment",
                    "source": "Oncology Guidelines",
                    "category": "Oncology",
                    "keywords": ["cancer", "oncology", "treatment", "screening"]
                }
            }
        ]
        
        for doc in sample_docs:
            await self.add_document(doc["content"], doc["metadata"])
        
        logger.info("Added sample medical documents to vector store")

# Global instance
vector_service = VectorService()
