"""
PubMed Integration Service
Handles fetching and processing medical literature from PubMed
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class PubMedService:
    def __init__(self):
        """Initialize PubMed service"""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.esearch_url = f"{self.base_url}esearch.fcgi"
        self.efetch_url = f"{self.base_url}efetch.fcgi"
        
        # Rate limiting
        self.request_delay = 0.34  # 3 requests per second max
    
    async def search_articles(
        self, 
        query: str, 
        max_results: int = 10,
        date_range: Optional[str] = None,
        article_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed for articles
        
        Args:
            query: Search query
            max_results: Maximum number of results
            date_range: Date range filter (e.g., "2020:2024")
            article_type: Article type filter
            
        Returns:
            List of article metadata
        """
        try:
            # Build search query
            search_query = self._build_search_query(query, date_range, article_type)
            
            # Search for article IDs
            pmids = await self._search_pmids(search_query, max_results)
            
            if not pmids:
                return []
            
            # Fetch article details
            articles = await self._fetch_article_details(pmids)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    def _build_search_query(self, query: str, date_range: Optional[str] = None, article_type: Optional[str] = None) -> str:
        """Build PubMed search query"""
        
        # Clean and format query
        clean_query = re.sub(r'[^\w\s]', '', query)
        
        # Add filters
        filters = []
        
        if date_range:
            filters.append(f"({date_range}[PDAT])")
        
        if article_type:
            filters.append(f"({article_type}[PT])")
        
        # Combine query with filters
        if filters:
            return f"{clean_query} AND {' AND '.join(filters)}"
        
        return clean_query
    
    async def _search_pmids(self, query: str, max_results: int) -> List[str]:
        """Search for PMIDs using ESearch"""
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        }
        
        async with aiohttp.ClientSession() as session:
            await asyncio.sleep(self.request_delay)  # Rate limiting
            
            async with session.get(self.esearch_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("esearchresult", {}).get("idlist", [])
                else:
                    logger.error(f"ESearch failed with status {response.status}")
                    return []
    
    async def _fetch_article_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed article information using EFetch"""
        
        if not pmids:
            return []
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        async with aiohttp.ClientSession() as session:
            await asyncio.sleep(self.request_delay)  # Rate limiting
            
            async with session.get(self.efetch_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_xml_articles(xml_content)
                else:
                    logger.error(f"EFetch failed with status {response.status}")
                    return []
    
    def _parse_xml_articles(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse XML response to extract article details"""
        
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall(".//PubmedArticle"):
                article_data = self._extract_article_data(article)
                if article_data:
                    articles.append(article_data)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing PubMed XML: {e}")
        
        return articles
    
    def _extract_article_data(self, article_element) -> Optional[Dict[str, Any]]:
        """Extract article data from XML element"""
        
        try:
            # Extract PMID
            pmid_elem = article_element.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
            
            # Extract title
            title_elem = article_element.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"
            
            # Extract authors
            authors = []
            for author in article_element.findall(".//Author"):
                last_name = author.find("LastName")
                first_name = author.find("ForeName")
                if last_name is not None:
                    author_name = last_name.text
                    if first_name is not None:
                        author_name += f", {first_name.text}"
                    authors.append(author_name)
            
            # Extract journal
            journal_elem = article_element.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"
            
            # Extract publication date
            pub_date = self._extract_publication_date(article_element)
            
            # Extract abstract
            abstract_elem = article_element.find(".//AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            # Extract DOI
            doi = self._extract_doi(article_element)
            
            # Extract keywords
            keywords = self._extract_keywords(article_element)
            
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "publication_date": pub_date,
                "abstract": abstract,
                "doi": doi,
                "keywords": keywords,
                "source": "PubMed",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "verified": True
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def _extract_publication_date(self, article_element) -> str:
        """Extract publication date from article element"""
        
        try:
            # Try to get publication date
            pub_date = article_element.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                day = pub_date.find("Day")
                
                if year is not None:
                    date_parts = [year.text]
                    if month is not None:
                        date_parts.append(month.text)
                    if day is not None:
                        date_parts.append(day.text)
                    return "/".join(date_parts)
            
            return "Unknown date"
            
        except Exception as e:
            logger.error(f"Error extracting publication date: {e}")
            return "Unknown date"
    
    def _extract_doi(self, article_element) -> str:
        """Extract DOI from article element"""
        
        try:
            # Look for DOI in article IDs
            for article_id in article_element.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    return article_id.text
            
            return "No DOI available"
            
        except Exception as e:
            logger.error(f"Error extracting DOI: {e}")
            return "No DOI available"
    
    def _extract_keywords(self, article_element) -> List[str]:
        """Extract keywords from article element"""
        
        try:
            keywords = []
            for keyword in article_element.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text.strip())
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def get_article_by_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Get a specific article by PMID"""
        
        articles = await self._fetch_article_details([pmid])
        return articles[0] if articles else None
    
    async def search_recent_articles(self, query: str, days: int = 30) -> List[Dict[str, Any]]:
        """Search for recent articles within specified days"""
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        date_range = f"{start_date.year}:{end_date.year}"
        
        return await self.search_articles(query, date_range=date_range)
    
    async def get_related_articles(self, pmid: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get articles related to a specific PMID"""
        
        try:
            # This is a simplified implementation
            # In practice, you might use PubMed's related articles API or other methods
            
            # For demo purposes, we'll search for similar terms
            article = await self.get_article_by_pmid(pmid)
            if not article:
                return []
            
            # Extract key terms from title and abstract
            title_words = article["title"].split()[:5]  # First 5 words
            query = " ".join(title_words)
            
            # Search for similar articles
            related = await self.search_articles(query, max_results)
            
            # Remove the original article
            related = [art for art in related if art["pmid"] != pmid]
            
            return related[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting related articles: {e}")
            return []

# Global instance
pubmed_service = PubMedService()
