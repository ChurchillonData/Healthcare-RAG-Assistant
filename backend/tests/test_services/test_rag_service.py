"""
RAG service tests
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.rag_service import RAGService

class TestRAGService:
    """Test RAG service functionality"""
    
    @pytest.fixture
    def rag_service(self):
        """Create RAG service instance"""
        return RAGService()
    
    @pytest.mark.asyncio
    async def test_search_relevant_documents(self, rag_service):
        """Test searching for relevant documents"""
        with patch.object(rag_service, '_get_embedding', new_callable=AsyncMock) as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3]
            
            results = await rag_service.search_relevant_documents("test query", limit=3)
            
            assert isinstance(results, list)
            # Should return mock results since we're not actually connected to a vector DB
            assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_generate_response(self, rag_service):
        """Test generating AI response"""
        mock_documents = [
            {
                "id": "doc_1",
                "title": "Test Document",
                "content": "Test content",
                "source": "test.pdf",
                "relevance_score": 0.9
            }
        ]
        
        with patch.object(rag_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Test AI response"
            mock_response.usage.total_tokens = 100
            mock_create.return_value = mock_response
            
            result = await rag_service.generate_response(
                query="test query",
                context_documents=mock_documents
            )
            
            assert "response" in result
            assert "citations" in result
            assert "tokens_used" in result
            assert result["response"] == "Test AI response"
            assert len(result["citations"]) == 1
    
    @pytest.mark.asyncio
    async def test_generate_response_with_history(self, rag_service):
        """Test generating response with conversation history"""
        mock_documents = []
        conversation_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        with patch.object(rag_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Test AI response"
            mock_response.usage.total_tokens = 100
            mock_create.return_value = mock_response
            
            result = await rag_service.generate_response(
                query="test query",
                context_documents=mock_documents,
                conversation_history=conversation_history
            )
            
            assert "response" in result
            # Verify that conversation history was included in the request
            call_args = mock_create.call_args
            messages = call_args[1]["messages"]
            assert len(messages) > 3  # system + history + user message
    
    def test_build_context(self, rag_service):
        """Test building context from documents"""
        documents = [
            {
                "title": "Document 1",
                "content": "Content 1",
                "source": "source1.pdf"
            },
            {
                "title": "Document 2", 
                "content": "Content 2",
                "source": "source2.pdf"
            }
        ]
        
        context = rag_service._build_context(documents)
        
        assert "[1]" in context
        assert "[2]" in context
        assert "Document 1" in context
        assert "Document 2" in context
        assert "Content 1" in context
        assert "Content 2" in context
    
    def test_generate_citations(self, rag_service):
        """Test generating citations"""
        documents = [
            {
                "id": "doc_1",
                "title": "Test Document",
                "source": "test.pdf",
                "page": 1,
                "relevance_score": 0.9
            }
        ]
        
        citations = rag_service._generate_citations(documents, "test response")
        
        assert len(citations) == 1
        assert citations[0]["id"] == "doc_1"
        assert citations[0]["title"] == "Test Document"
        assert citations[0]["relevance_score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_summarize_document(self, rag_service):
        """Test document summarization"""
        document_content = "This is a long document with lots of content that needs to be summarized."
        
        with patch.object(rag_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "This is a summary."
            mock_create.return_value = mock_response
            
            summary = await rag_service.summarize_document(document_content, max_length=50)
            
            assert summary == "This is a summary."
    
    @pytest.mark.asyncio
    async def test_extract_keywords(self, rag_service):
        """Test keyword extraction"""
        text = "This is a document about artificial intelligence and machine learning in healthcare."
        
        with patch.object(rag_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "artificial intelligence, machine learning, healthcare"
            mock_create.return_value = mock_response
            
            keywords = await rag_service.extract_keywords(text, num_keywords=3)
            
            assert isinstance(keywords, list)
            assert len(keywords) == 3
            assert "artificial intelligence" in keywords
