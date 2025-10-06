"""
OpenAI Service for Healthcare AI
Handles OpenAI API integration for medical responses
"""

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

import asyncio
from typing import List, Dict, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI service with API key from settings"""
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        
        if not self.api_key or self.api_key == "your-openai-api-key-here" or not openai:
            logger.warning("OpenAI API key not configured or OpenAI package not installed. Using placeholder responses.")
            self.api_key = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    async def generate_medical_response(
        self, 
        query: str, 
        context_documents: List[str] = None,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a medical response using OpenAI GPT
        
        Args:
            query: The medical question from the user
            context_documents: Retrieved medical documents for context
            conversation_history: Previous conversation messages
            
        Returns:
            Dict containing response, sources, and metadata
        """
        
        if not self.client:
            return self._get_placeholder_response(query)
        
        try:
            # Build the prompt with medical context
            prompt = self._build_medical_prompt(query, context_documents)
            
            # Prepare conversation history
            messages = self._prepare_messages(prompt, conversation_history)
            
            # Call OpenAI API
            response = await self._call_openai_api(messages)
            
            # Extract and format response
            return self._format_response(response, context_documents)
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return self._get_error_response(query, str(e))
    
    def _build_medical_prompt(self, query: str, context_documents: List[str] = None) -> str:
        """Build a comprehensive medical prompt"""
        
        base_prompt = """You are a professional medical AI assistant specialized in healthcare information. 
        You provide accurate, evidence-based medical information while always recommending users consult healthcare professionals for medical decisions.

        Guidelines:
        1. Provide evidence-based medical information
        2. Always recommend consulting healthcare professionals for medical decisions
        3. Cite sources when available
        4. Be clear about limitations of AI medical advice
        5. Prioritize patient safety
        6. Use appropriate medical terminology while remaining accessible

        User Question: {query}
        """.format(query=query)
        
        if context_documents:
            base_prompt += "\n\nRelevant Medical Literature:\n"
            for i, doc in enumerate(context_documents, 1):
                base_prompt += f"{i}. {doc}\n"
        
        base_prompt += "\n\nPlease provide a comprehensive, evidence-based response to the medical question above."
        
        return base_prompt
    
    def _prepare_messages(self, prompt: str, conversation_history: List[Dict] = None) -> List[Dict]:
        """Prepare messages for OpenAI API"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional medical AI assistant. Provide accurate, evidence-based medical information while emphasizing the importance of consulting healthcare professionals for medical decisions."
            }
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-6:]:  # Limit to last 6 messages
                messages.append({
                    "role": "user" if msg.get("sender") == "user" else "assistant",
                    "content": msg.get("content", "")
                })
        
        # Add current query
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return messages
    
    async def _call_openai_api(self, messages: List[Dict]) -> str:
        """Call OpenAI API asynchronously"""
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",  # Use GPT-4 for better medical responses
                messages=messages,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more consistent medical responses
                top_p=0.9
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise e
    
    def _format_response(self, response: str, context_documents: List[str] = None) -> Dict[str, Any]:
        """Format the OpenAI response"""
        
        return {
            "response": response,
            "sources": context_documents or [],
            "ai_model": "gpt-4",
            "confidence": "high" if context_documents else "medium",
            "disclaimer": "This information is for educational purposes only and should not replace professional medical advice."
        }
    
    def _get_placeholder_response(self, query: str) -> Dict[str, Any]:
        """Return helpful response when OpenAI is not configured"""
        
        # Provide a more helpful response based on the query
        query_lower = query.lower()
        
        if "diabetes" in query_lower:
            response = """I understand you're asking about diabetes. While my full AI capabilities aren't configured yet, I can help you find relevant medical research.

**Common Diabetes Symptoms:**
- Increased thirst and urination
- Unexplained weight loss
- Fatigue and weakness
- Blurred vision
- Slow-healing sores

**Important:** This is general information. For personalized medical advice, please consult a healthcare professional.

**To get more detailed information:**
1. Use the search function above to find research papers on diabetes
2. Look for the green "PubMed" badges for peer-reviewed studies
3. Click on DOI or PMID links to access full papers

Would you like me to search our medical literature database for specific diabetes-related research?"""
        
        elif "symptoms" in query_lower:
            response = f"""I understand you're asking about symptoms related to: '{query}'. 

While my full AI capabilities aren't configured yet, I can help you find relevant medical research from our database of 200K+ PubMed abstracts.

**To get detailed symptom information:**
1. Use the search function above to find research papers
2. Look for the green "PubMed" badges for peer-reviewed studies
3. Click on DOI or PMID links to access full medical papers

**Important:** Always consult a healthcare professional for medical advice and diagnosis.

Would you like me to search our medical literature for research on this topic?"""
        
        else:
            response = f"""I understand you're asking about: '{query}'. 

While my full AI capabilities aren't configured yet, I can help you search through our comprehensive medical literature database containing 200K+ PubMed research abstracts.

**To get detailed information:**
1. Use the search function above to find relevant research papers
2. Look for the green "PubMed" badges for peer-reviewed studies
3. Click on DOI or PMID links to access full medical papers

**Important:** Always consult a healthcare professional for personalized medical advice.

Would you like me to search our medical literature database for research on this topic?"""
        
        return {
            "response": response,
            "sources": [],
            "ai_model": "medical_literature_search",
            "confidence": "medium",
            "disclaimer": "This response provides general information and search guidance. For medical advice, consult a healthcare professional."
        }
    
    def _get_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        
        return {
            "response": f"I apologize, but I encountered an error while processing your medical question: '{query}'. Error: {error}. Please try again or consult a healthcare professional.",
            "sources": [],
            "ai_model": "error",
            "confidence": "none",
            "disclaimer": "This response indicates an error. Please consult a healthcare professional for medical advice."
        }
    
    async def generate_medical_summary(self, documents: List[str]) -> str:
        """Generate a summary of medical documents"""
        
        if not self.client:
            return "Summary generation requires OpenAI API configuration."
        
        try:
            prompt = f"""Please provide a concise summary of the following medical documents:

            {chr(10).join(documents)}

            Focus on:
            1. Key medical findings
            2. Important clinical implications
            3. Relevant treatment considerations
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating medical summary: {e}")
            return f"Error generating summary: {e}"

# Global instance
openai_service = OpenAIService()
