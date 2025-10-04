"""
RAG (Retrieval-Augmented Generation) service
"""

import asyncio
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RAGService:
    """RAG service for document retrieval and response generation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL
        self.chat_model = settings.CHAT_MODEL
    
    async def search_relevant_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic search"""
        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            
            # Here you would typically search your vector database
            # For now, we'll return mock results
            mock_documents = [
                {
                    "id": "doc_1",
                    "title": "Healthcare AI Applications",
                    "content": "Artificial intelligence is revolutionizing healthcare through various applications...",
                    "relevance_score": 0.95,
                    "source": "medical_journal_2023.pdf",
                    "page": 1
                },
                {
                    "id": "doc_2", 
                    "title": "Medical Diagnosis with AI",
                    "content": "AI-powered diagnostic tools are improving accuracy and speed in medical diagnosis...",
                    "relevance_score": 0.88,
                    "source": "ai_healthcare_guide.pdf",
                    "page": 15
                }
            ]
            
            return mock_documents[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def generate_response(
        self, 
        query: str, 
        context_documents: List[Dict[str, Any]], 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate AI response using retrieved context"""
        try:
            # Build context from documents
            context = self._build_context(context_documents)
            
            # Build conversation history
            history = conversation_history or []
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful healthcare AI assistant. Use the provided context documents to answer questions accurately and cite your sources. If you cannot find relevant information in the context, say so clearly."""
                }
            ]
            
            # Add conversation history
            for msg in history[-10:]:  # Limit to last 10 messages
                messages.append(msg)
            
            # Add current query with context
            messages.append({
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {query}"
            })
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Generate citations
            citations = self._generate_citations(context_documents, response_content)
            
            return {
                "response": response_content,
                "citations": citations,
                "tokens_used": response.usage.total_tokens,
                "model_used": self.chat_model
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I apologize, but I'm having trouble generating a response right now. Please try again later.",
                "citations": [],
                "tokens_used": 0,
                "model_used": self.chat_model
            }
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from documents"""
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[{i}] {doc.get('title', 'Untitled')}\n"
                f"Source: {doc.get('source', 'Unknown')}\n"
                f"Content: {doc.get('content', '')}\n"
            )
        
        return "\n".join(context_parts)
    
    def _generate_citations(self, documents: List[Dict[str, Any]], response: str) -> List[Dict[str, Any]]:
        """Generate citations for the response"""
        citations = []
        
        for doc in documents:
            citation = {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "source": doc.get("source"),
                "page": doc.get("page"),
                "relevance_score": doc.get("relevance_score", 0.0)
            }
            citations.append(citation)
        
        return citations
    
    async def summarize_document(self, document_content: str, max_length: int = 200) -> str:
        """Summarize a document"""
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Summarize the following document in no more than {max_length} words, focusing on key points:"
                    },
                    {
                        "role": "user",
                        "content": document_content
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return "Unable to generate summary."
    
    async def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Extract the top {num_keywords} most important keywords from the following text. Return only the keywords separated by commas:"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            keywords = response.choices[0].message.content.split(",")
            return [keyword.strip() for keyword in keywords if keyword.strip()]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
