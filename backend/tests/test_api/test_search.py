"""
Search API tests
"""

import pytest
from fastapi.testclient import TestClient

class TestSearchAPI:
    """Test search endpoints"""
    
    def test_search_documents(self, client: TestClient, sample_search_request):
        """Test document search"""
        response = client.post("/api/v1/search/documents", json=sample_search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_results" in data
        assert "search_time_ms" in data
        assert isinstance(data["documents"], list)
    
    def test_search_with_filters(self, client: TestClient):
        """Test search with filters"""
        search_request = {
            "query": "artificial intelligence healthcare",
            "filters": {
                "document_types": ["journal", "book"],
                "min_relevance_score": 0.8
            },
            "limit": 5
        }
        
        response = client.post("/api/v1/search/documents", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "filters_applied" in data
    
    def test_get_search_suggestions(self, client: TestClient):
        """Test getting search suggestions"""
        response = client.get("/api/v1/search/suggestions?q=health&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_get_search_filters(self, client: TestClient):
        """Test getting available search filters"""
        response = client.get("/api/v1/search/filters")
        
        assert response.status_code == 200
        data = response.json()
        assert "filters" in data
        assert isinstance(data["filters"], dict)
    
    def test_get_trending_searches(self, client: TestClient):
        """Test getting trending searches"""
        response = client.get("/api/v1/search/trending?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "trending_searches" in data
        assert isinstance(data["trending_searches"], list)
    
    def test_submit_search_feedback(self, client: TestClient):
        """Test submitting search feedback"""
        feedback_data = {
            "search_id": "test-search-id",
            "rating": 4,
            "feedback": "Good results"
        }
        
        response = client.post("/api/v1/search/feedback", json=feedback_data)
        
        # This might return 404 if search_id doesn't exist, which is expected
        assert response.status_code in [200, 404]
    
    def test_search_invalid_query(self, client: TestClient):
        """Test search with invalid query"""
        search_request = {
            "query": "",  # Empty query
            "limit": 10
        }
        
        response = client.post("/api/v1/search/documents", json=search_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_search_invalid_limit(self, client: TestClient):
        """Test search with invalid limit"""
        search_request = {
            "query": "test query",
            "limit": 1000  # Too high
        }
        
        response = client.post("/api/v1/search/documents", json=search_request)
        
        assert response.status_code == 422  # Validation error
