import logging
from typing import List, Dict
import warnings
# Suppress the duckduckgo_search renaming warning
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
from duckduckgo_search import DDGS
from app.tools.base import BaseTool

class EnhancedWebSearchTool(BaseTool):
    """Enhanced tool for performing web searches with multiple strategies."""
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches the web for information on a given query with multiple search strategies and language filtering."
        )

    def _filter_non_english_results(self, results: List[Dict]) -> List[Dict]:
        """Filter out non-English results based on title and content analysis."""
        filtered_results = []
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', result.get('body', ''))
            
            # Basic language detection - check if result contains mostly English characters
            combined_text = f"{title} {snippet}"
            english_chars = sum(1 for char in combined_text if char.isascii() and char.isalpha())
            total_chars = sum(1 for char in combined_text if char.isalpha())
            
            # If more than 70% of alphabetic characters are ASCII, consider it English
            if total_chars > 0 and (english_chars / total_chars) >= 0.7:
                filtered_results.append(result)
        
        return filtered_results

    def _enhance_query(self, query: str) -> List[str]:
        """Generate multiple enhanced queries for better search results."""
        enhanced_queries = [query]
        
        # Add specific search operators and variations
        if "most" in query.lower() and ("liked" in query.lower() or "popular" in query.lower()):
            enhanced_queries.extend([
                f"{query} site:instagram.com",
                f"{query} official statistics",
                f"{query} 2024 2025",
                f"{query} record breaking",
                f'"{query}" -site:baidu.com -site:zhihu.com'
            ])
        elif "stock" in query.lower() or "price" in query.lower():
            enhanced_queries.extend([
                f"{query} today current",
                f"{query} real time",
                f"{query} market data"
            ])
        elif "news" in query.lower():
            enhanced_queries.extend([
                f"{query} latest breaking",
                f"{query} today 2025",
                f"{query} recent updates"
            ])
        else:
            enhanced_queries.extend([
                f"{query} 2025",
                f"{query} latest information",
                f'"{query}" official'
            ])
        
        return enhanced_queries[:3]  # Limit to 3 queries

    async def execute(self, query: str, num_results: int = 8) -> List[Dict[str, str]]:
        logging.info(f"Executing enhanced web search for query: {query}")
        all_results = []
        
        try:
            enhanced_queries = self._enhance_query(query)
            
            for search_query in enhanced_queries:
                try:
                    with DDGS() as ddgs:
                        # Search with region preference for English results
                        results = [r for r in ddgs.text(
                            search_query, 
                            max_results=num_results,
                            region='us-en',  # Prefer US English results
                            safesearch='moderate'
                        )]
                        
                        for result in results:
                            formatted_result = {
                                "title": result.get('title', ''),
                                "snippet": result.get('body', ''),
                                "url": result.get('href', ''),
                                "query_used": search_query
                            }
                            all_results.append(formatted_result)
                
                except Exception as e:
                    logging.warning(f"Error with query '{search_query}': {e}")
                    continue
            
            # Filter non-English results
            filtered_results = self._filter_non_english_results(all_results)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_results = []
            for result in filtered_results:
                url = result.get('url', '')
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # Sort by relevance (prioritize exact matches and official sources)
            def relevance_score(result):
                score = 0
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                url = result.get('url', '').lower()
                
                # Prioritize official sources
                if any(domain in url for domain in ['instagram.com', 'facebook.com', 'twitter.com', 'linkedin.com']):
                    score += 10
                
                # Prioritize recent content
                if any(year in title + snippet for year in ['2024', '2025']):
                    score += 5
                
                # Prioritize exact query matches
                query_words = query.lower().split()
                title_words = title.split()
                if all(word in title_words for word in query_words):
                    score += 8
                
                return score
            
            unique_results.sort(key=relevance_score, reverse=True)
            
            return unique_results[:num_results] if unique_results else [
                {"error": "No relevant English results found for this query"}
            ]
            
        except Exception as e:
            logging.error(f"Error during enhanced web search: {e}")
            return [{"error": str(e)}]

class EnhancedNewsSearchTool(BaseTool):
    """Enhanced tool for searching recent news with better filtering."""
    def __init__(self):
        super().__init__(
            name="news_search",
            description="Searches for recent news articles with enhanced filtering and relevance."
        )

    async def execute(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        logging.info(f"Executing enhanced news search for query: {query}")
        try:
            with DDGS() as ddgs:
                # Multiple search attempts with different time ranges
                results = []
                
                # Try recent news first
                try:
                    recent_results = [r for r in ddgs.news(
                        query, 
                        max_results=num_results * 2,
                        region='us-en',
                        safesearch='moderate'
                    )]
                    results.extend(recent_results)
                except:
                    pass
                
                # If not enough results, try broader search
                if len(results) < num_results:
                    try:
                        broader_results = [r for r in ddgs.news(
                            f"{query} news", 
                            max_results=num_results,
                            region='us-en'
                        )]
                        results.extend(broader_results)
                    except:
                        pass
                
                formatted_results = []
                seen_urls = set()
                
                for result in results:
                    url = result.get('url', '')
                    if url not in seen_urls:
                        seen_urls.add(url)
                        formatted_results.append({
                            "title": result.get('title', ''),
                            "source": result.get('source', ''),
                            "date": result.get('date', ''),
                            "url": url,
                            "snippet": result.get('body', '')[:200] + "..." if result.get('body') else ""
                        })
                
                return formatted_results[:num_results] if formatted_results else [
                    {"error": "No recent news found for this query"}
                ]
                
        except Exception as e:
            logging.error(f"Error during enhanced news search: {e}")
            return [{"error": str(e)}]

class SocialMediaSearchTool(BaseTool):
    """Tool specifically for social media related queries."""
    def __init__(self):
        super().__init__(
            name="social_media_search",
            description="Searches for social media statistics, trends, and information from platforms like Instagram, Twitter, TikTok, etc."
        )

    async def execute(self, query: str, platform: str = "instagram") -> List[Dict[str, str]]:
        logging.info(f"Executing social media search for: {query} on {platform}")
        try:
            # Construct platform-specific search queries
            search_queries = [
                f"{query} site:{platform}.com",
                f"{query} {platform} official statistics",
                f"{query} {platform} records data",
                f'"{query}" {platform} -site:baidu.com -site:zhihu.com'
            ]
            
            all_results = []
            
            with DDGS() as ddgs:
                for search_query in search_queries:
                    try:
                        results = [r for r in ddgs.text(
                            search_query,
                            max_results=3,
                            region='us-en'
                        )]
                        
                        for result in results:
                            all_results.append({
                                "title": result.get('title', ''),
                                "snippet": result.get('body', ''),
                                "url": result.get('href', ''),
                                "platform": platform,
                                "search_query": search_query
                            })
                    except:
                        continue
            
            # Remove duplicates and filter for relevance
            seen_urls = set()
            unique_results = []
            
            for result in all_results:
                url = result.get('url', '')
                if url not in seen_urls and platform in result.get('url', '').lower():
                    seen_urls.add(url)
                    unique_results.append(result)
            
            return unique_results[:5] if unique_results else [
                {"error": f"No {platform} specific results found for this query"}
            ]
            
        except Exception as e:
            logging.error(f"Error during social media search: {e}")
            return [{"error": str(e)}]
