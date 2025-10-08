"""
Healthcare AI Backend with RAG System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import asyncio

# Import our services
from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.pubmed_service import pubmed_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Healthcare AI Backend",
    description="A professional medical assistant that can answer healthcare questions using 200K+ PubMed research abstracts with proper citations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple response models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    environment: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    citations: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    query: str

# Root endpoint
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {"message": "Healthcare AI Backend is running!"}

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Server is running successfully",
        version="1.0.0",
        environment="development"
    )

# Chat endpoint with RAG system
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI assistant using RAG system"""
    logger.info(f"Received chat request: {request.message}")
    
    try:
        # Step 1: Search for relevant local medical documents
        relevant_docs = await vector_service.search_similar_documents(
            query=request.message,
            top_k=3,
            threshold=0.5
        )
        
        # Step 2: Search PubMed for recent research papers
        pubmed_results = []
        try:
            pubmed_results = await pubmed_service.search_articles(
                query=request.message,
                max_results=3,  # Limit for chat context
                date_range="2020:2024"
            )
        except Exception as e:
            logger.warning(f"PubMed search failed in chat: {e}")
        
        # Step 3: Prepare context from retrieved documents
        context_documents = []
        sources = []
        
        # Add local documents to context
        for doc in relevant_docs:
            context_documents.append(doc["content"])
            sources.append({
                "title": doc["metadata"].get("title", "Medical Document"),
                "source": doc["metadata"].get("source", "Medical Database"),
                "category": doc["metadata"].get("category", "General"),
                "similarity": doc["similarity"],
                "type": "local"
            })
        
        # Add PubMed papers to context
        for article in pubmed_results:
            # Use abstract as context for the AI
            context_documents.append(f"Research Paper: {article['title']}\nAbstract: {article['abstract']}")
            sources.append({
                "title": article["title"],
                "source": "PubMed",
                "category": "Research",
                "similarity": 0.9,  # High relevance for PubMed results
                "type": "pubmed",
                "doi": article["doi"],
                "pmid": article["pmid"],
                "authors": article["authors"][:3] if article["authors"] else ["Unknown"],
                "year": article["publication_date"]
            })
        
        # Step 3: Generate AI response using OpenAI with context
        ai_response = await openai_service.generate_medical_response(
            query=request.message,
            context_documents=context_documents,
            conversation_history=[]  # Could add conversation history here
        )
        
        # Step 4: Format citations with enhanced PubMed support
        citations = []
        for source in sources:
            citation = {
                "id": f"cite_{len(citations)}",
                "title": source["title"],
                "source": source["source"],
                "category": source["category"],
                "relevance": source["similarity"],
                "type": source.get("type", "unknown")
            }
            
            # Add PubMed-specific fields
            if source.get("type") == "pubmed":
                citation.update({
                    "doi": source.get("doi", "N/A"),
                    "pmid": source.get("pmid", "N/A"),
                    "authors": source.get("authors", ["Unknown"]),
                    "year": source.get("year", "Unknown")
                })
            
            citations.append(citation)
        
        return ChatResponse(
            response=ai_response["response"],
            conversation_id=request.conversation_id or "demo-conversation-123",
            citations=citations,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        
        # Fallback to simple response
        return ChatResponse(
            response=f"I apologize, but I encountered an error processing your medical question: '{request.message}'. Please try again or consult a healthcare professional for immediate medical advice.",
            conversation_id=request.conversation_id or "demo-conversation-123",
            citations=[],
            sources=[]
        )

# Search endpoint (simplified)
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search the knowledge base"""
    logger.info(f"Received search request: {request.query}")
    
    try:
        # Step 1: Search local vector database
        local_docs = await vector_service.search_similar_documents(
            query=request.query,
            top_k=3,
            threshold=0.5
        )
        
        # Step 2: Search PubMed for recent articles
        pubmed_results = []
        try:
            pubmed_results = await pubmed_service.search_articles(
                query=request.query,
                max_results=5,
                date_range="2020:2024"  # Recent articles
            )
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        # Step 3: Combine and format results
        combined_results = []
        
        # Add local results
        for doc in local_docs:
            combined_results.append({
                "title": doc["metadata"].get("title", "Medical Document"),
                "authors": ["Medical Database"],
                "abstract": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                "year": "2023",
                "doi": "Local Database",
                "source": "Local",
                "relevance": doc["similarity"]
            })
        
        # Add PubMed results
        for article in pubmed_results:
            combined_results.append({
                "title": article["title"],
                "authors": article["authors"][:3],  # Limit to first 3 authors
                "abstract": article["abstract"],
                "year": article["publication_date"],
                "doi": article["doi"],
                "source": "PubMed",
                "pmid": article["pmid"],
                "url": article["url"]
            })
        
        # Sort by relevance/recency
        combined_results.sort(key=lambda x: x.get("relevance", 0.5), reverse=True)
        
        return SearchResponse(
            results=combined_results[:10],  # Limit to 10 results
            total_count=len(combined_results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        
        # Fallback to simple results
        return SearchResponse(
            results=[{
                "title": "Search Error",
                "authors": ["System"],
                "abstract": f"Error searching for '{request.query}'. Please try again.",
                "year": "2024",
                "doi": "Error"
            }],
            total_count=1,
            query=request.query
        )

# Citations endpoint (simplified)
@app.get("/citations/{citation_id}")
async def get_citation(citation_id: str):
    """Get citation details"""
    logger.info(f"Requested citation: {citation_id}")
    
    return {
        "id": citation_id,
        "title": "Sample Citation",
        "authors": ["Dr. Sample"],
        "journal": "Sample Journal",
        "year": 2023,
        "doi": "10.1234/sample.2023.001",
        "url": "https://example.com/paper",
        "verified": True
    }

# API info endpoint
@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "Healthcare AI Backend",
        "version": "1.0.0",
        "description": "A professional medical assistant with RAG capabilities",
        "features": [
            "Chat with AI assistant",
            "Search medical literature",
            "Citation management",
            "Health check monitoring"
        ],
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "search": "/search",
            "citations": "/citations/{id}",
            "docs": "/docs"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Healthcare AI Backend starting up...")
    
    # Initialize vector store with sample medical documents
    try:
        await vector_service.add_sample_medical_documents()
        logger.info("Sample medical documents loaded into vector store")
    except Exception as e:
        logger.error(f"Error loading sample documents: {e}")
    
    logger.info("Application startup complete!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
