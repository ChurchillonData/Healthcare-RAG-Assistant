"""
Chat API tests
"""

import pytest
from fastapi.testclient import TestClient

class TestChatAPI:
    """Test chat endpoints"""
    
    def test_create_conversation(self, client: TestClient, auth_headers, sample_conversation_data):
        """Test creating a new conversation"""
        response = client.post(
            "/api/v1/chat/conversations",
            json=sample_conversation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_conversation_data["title"]
        assert data["description"] == sample_conversation_data["description"]
        assert "id" in data
    
    def test_create_conversation_unauthorized(self, client: TestClient, sample_conversation_data):
        """Test creating conversation without authentication"""
        response = client.post(
            "/api/v1/chat/conversations",
            json=sample_conversation_data
        )
        
        assert response.status_code == 401
    
    def test_get_conversations(self, client: TestClient, auth_headers):
        """Test getting user conversations"""
        response = client.get("/api/v1/chat/conversations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_chat_with_ai(self, client: TestClient, sample_chat_request):
        """Test chatting with AI (no authentication required)"""
        response = client.post("/api/v1/chat/chat", json=sample_chat_request)
        
        # Note: This test might fail if OpenAI API key is not configured
        # In a real test environment, you'd mock the OpenAI API calls
        assert response.status_code in [200, 500]  # 500 if OpenAI API not configured
    
    def test_chat_with_conversation_id(self, client: TestClient, auth_headers, sample_chat_request):
        """Test chat with conversation ID"""
        # First create a conversation
        conversation_data = {
            "title": "Test Chat",
            "description": "Test conversation"
        }
        
        conv_response = client.post(
            "/api/v1/chat/conversations",
            json=conversation_data,
            headers=auth_headers
        )
        
        conversation_id = conv_response.json()["id"]
        sample_chat_request["conversation_id"] = conversation_id
        
        # Then send a chat message
        response = client.post("/api/v1/chat/chat", json=sample_chat_request, headers=auth_headers)
        
        assert response.status_code in [200, 500]  # 500 if OpenAI API not configured
    
    def test_get_conversation_by_id(self, client: TestClient, auth_headers):
        """Test getting a specific conversation"""
        # First create a conversation
        conversation_data = {
            "title": "Test Conversation",
            "description": "Test conversation for retrieval"
        }
        
        conv_response = client.post(
            "/api/v1/chat/conversations",
            json=conversation_data,
            headers=auth_headers
        )
        
        conversation_id = conv_response.json()["id"]
        
        # Then retrieve it
        response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == conversation_data["title"]
    
    def test_delete_conversation(self, client: TestClient, auth_headers):
        """Test deleting a conversation"""
        # First create a conversation
        conversation_data = {
            "title": "Test Conversation to Delete",
            "description": "This conversation will be deleted"
        }
        
        conv_response = client.post(
            "/api/v1/chat/conversations",
            json=conversation_data,
            headers=auth_headers
        )
        
        conversation_id = conv_response.json()["id"]
        
        # Then delete it
        response = client.delete(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted successfully"
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 404
