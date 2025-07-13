import requests
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from pathlib import Path

from core.base_tool import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Web search tool with quality-based persistence and cache management."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize web search tool."""
        self.config = config
        
        # Search configuration
        self.max_results = config.get('max_results', 5)
        self.cache_results = config.get('cache_results', True)
        self.quality_threshold = config.get('quality_threshold', 0.8)
        self.cache_freshness_days = config.get('cache_freshness_days', 30)
        
        # Setup cache directory
        self.cache_dir = Path(config.get('cache_path', './data/web_cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Request settings
        self.timeout = config.get('timeout', 10)
        self.headers = {
            'User-Agent': 'AI-Agent-Base/1.0 (Educational Research Tool)'
        }
        
        # Note: This is a simplified implementation
        # In production, you would integrate with search APIs like:
        # - Google Search API
        # - Bing Search API
        # - DuckDuckGo API
        # - Tavily API
        # - SerpAPI
    
    @property
    def name(self) -> str:
        """Get the name of this tool."""
        return "web_search"
    
    @property
    def description(self) -> str:
        """Get a description of what this tool does."""
        return (
            "Searches the web for information and caches high-quality results. "
            "Automatically filters and persists relevant content based on quality metrics. "
            "Example: 'search for python pytest tutorials' or 'find latest news about AI'"
        )
    
    def execute(self, input_text: str, **kwargs) -> ToolResult:
        """Execute web search with the given query."""
        try:
            # Parse search query
            query = self._parse_search_query(input_text)
            
            if not query:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="Please provide a search query."
                )
            
            # Check cache first
            cached_results = self._check_cache(query)
            if cached_results:
                return ToolResult(
                    success=True,
                    content=self._format_search_results(cached_results),
                    metadata={
                        "query": query,
                        "source": "cache",
                        "results_count": len(cached_results),
                        "cached": True
                    }
                )
            
            # Perform web search
            search_results = self._perform_search(query)
            
            if not search_results:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="No search results found or search service unavailable."
                )
            
            # Process and cache high-quality results
            processed_results = self._process_search_results(query, search_results)
            
            # Cache results if they meet quality threshold
            if processed_results:
                self._cache_results(query, processed_results)
            
            return ToolResult(
                success=True,
                content=self._format_search_results(processed_results),
                metadata={
                    "query": query,
                    "source": "web_search",
                    "results_count": len(processed_results),
                    "cached": False
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Web search error: {str(e)}"
            )
    
    def _parse_search_query(self, input_text: str) -> str:
        """Parse and clean the search query."""
        # Remove common prefixes
        query = input_text.strip()
        
        prefixes = [
            'search for', 'search', 'find', 'look up', 'look for',
            'google', 'bing', 'web search', 'search web'
        ]
        
        query_lower = query.lower()
        for prefix in prefixes:
            if query_lower.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        return query
    
    def _check_cache(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Check if cached results exist for the query."""
        if not self.cache_results:
            return None
        
        try:
            cache_key = self._get_cache_key(query)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still fresh
            cache_date = datetime.fromisoformat(cache_data['cached_at'])
            age_days = (datetime.now() - cache_date).days
            
            if age_days > self.cache_freshness_days:
                # Cache is stale, remove it
                cache_file.unlink()
                return None
            
            return cache_data['results']
            
        except Exception:
            return None
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        return hashlib.md5(query.lower().encode('utf-8')).hexdigest()
    
    def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search using available search service.
        
        Note: This is a simplified implementation for demonstration.
        In production, integrate with a real search API.
        """
        # This is a mock implementation
        # In reality, you would call a search API here
        
        # For demonstration purposes, return mock results
        mock_results = [
            {
                "title": f"Search Result 1 for '{query}'",
                "url": "https://example.com/result1",
                "snippet": f"This is a mock search result for the query '{query}'. In a real implementation, this would come from a search API.",
                "source": "example.com"
            },
            {
                "title": f"Search Result 2 for '{query}'",
                "url": "https://example.org/result2", 
                "snippet": f"Another mock result discussing '{query}' with relevant information and context.",
                "source": "example.org"
            }
        ]
        
        # In production, replace with actual search API call:
        # results = self._call_search_api(query)
        
        return mock_results[:self.max_results]
    
    def _process_search_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process search results and assess quality."""
        processed_results = []
        
        for result in results:
            try:
                # Fetch content from URL
                content = self._fetch_url_content(result['url'])
                
                if not content:
                    continue
                
                # Assess content quality
                quality_score = self._assess_content_quality(query, result, content)
                
                # Only keep high-quality results
                if quality_score >= self.quality_threshold:
                    processed_result = {
                        "title": result['title'],
                        "url": result['url'],
                        "snippet": result['snippet'],
                        "content": content[:2000],  # First 2000 chars
                        "quality_score": quality_score,
                        "source": result.get('source', ''),
                        "fetched_at": datetime.now().isoformat()
                    }
                    processed_results.append(processed_result)
                    
            except Exception as e:
                # Log error but continue with other results
                continue
        
        return processed_results
    
    def _fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch content from URL."""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Simple text extraction (in production, use proper HTML parsing)
            content = response.text
            
            # Basic HTML tag removal (very simplified)
            import re
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except Exception:
            return None
    
    def _assess_content_quality(self, query: str, result: Dict[str, Any], content: str) -> float:
        """Assess content quality based on multiple factors."""
        score = 0.0
        
        # Factor 1: Semantic similarity (simplified)
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        title_words = set(result['title'].lower().split())
        
        # Calculate word overlap
        content_overlap = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
        title_overlap = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
        
        semantic_score = (content_overlap * 0.7 + title_overlap * 0.3)
        score += semantic_score * 0.4
        
        # Factor 2: Content length (reasonable length is better)
        length_score = min(len(content) / 1000, 1.0)  # Normalize to 1000 chars
        score += length_score * 0.2
        
        # Factor 3: Domain authority (simplified)
        domain = urlparse(result['url']).netloc
        authority_score = self._get_domain_authority_score(domain)
        score += authority_score * 0.2
        
        # Factor 4: Content structure (simplified)
        structure_score = self._assess_content_structure(content)
        score += structure_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_domain_authority_score(self, domain: str) -> float:
        """Get domain authority score (simplified)."""
        # In production, this could use real domain authority metrics
        high_authority_domains = {
            'wikipedia.org': 0.9,
            'github.com': 0.8,
            'stackoverflow.com': 0.8,
            'medium.com': 0.7,
            'arxiv.org': 0.9,
            'gov': 0.8,  # Government domains
            'edu': 0.8,  # Educational domains
        }
        
        for auth_domain, score in high_authority_domains.items():
            if auth_domain in domain:
                return score
        
        return 0.5  # Default score
    
    def _assess_content_structure(self, content: str) -> float:
        """Assess content structure quality."""
        score = 0.0
        
        # Check for structured content indicators
        if any(indicator in content.lower() for indicator in ['introduction', 'conclusion', 'summary']):
            score += 0.3
        
        # Check for lists or structured data
        if any(indicator in content for indicator in ['1.', '2.', '•', '-', '*']):
            score += 0.3
        
        # Check for reasonable paragraph structure
        paragraphs = content.split('\n')
        if len(paragraphs) > 3:
            score += 0.4
        
        return min(score, 1.0)
    
    def _cache_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Cache search results."""
        if not self.cache_results or not results:
            return
        
        try:
            cache_key = self._get_cache_key(query)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            cache_data = {
                "query": query,
                "cached_at": datetime.now().isoformat(),
                "results": results
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception:
            pass  # Fail silently for caching errors
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for display."""
        if not results:
            return "No search results found."
        
        formatted_parts = ["Search Results:\n"]
        
        for i, result in enumerate(results, 1):
            formatted_parts.append(f"{i}. **{result['title']}**")
            formatted_parts.append(f"   URL: {result['url']}")
            formatted_parts.append(f"   {result['snippet']}")
            
            if 'quality_score' in result:
                formatted_parts.append(f"   Quality Score: {result['quality_score']:.2f}")
            
            if 'fetched_at' in result:
                formatted_parts.append(f"   Fetched: {result['fetched_at'][:10]}")
            
            formatted_parts.append("")  # Empty line between results
        
        return "\n".join(formatted_parts)
    
    def get_usage_examples(self) -> List[str]:
        """Get examples of how to use this tool."""
        return [
            "search for python pytest tutorials",
            "find latest news about artificial intelligence",
            "look up React hooks documentation",
            "search machine learning best practices",
            "find information about climate change"
        ]
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Search query",
                    "examples": [
                        "search for python tutorials",
                        "find React documentation",
                        "look up machine learning"
                    ]
                }
            },
            "required": ["input"]
        }
    
    def cleanup_cache(self, max_age_days: int = None) -> int:
        """Clean up old cache files."""
        if max_age_days is None:
            max_age_days = self.cache_freshness_days
        
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            removed_count = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cache_date = datetime.fromisoformat(cache_data['cached_at'])
                    if cache_date < cutoff_date:
                        cache_file.unlink()
                        removed_count += 1
                        
                except Exception:
                    # Remove corrupted cache files
                    cache_file.unlink()
                    removed_count += 1
            
            return removed_count
            
        except Exception:
            return 0


# Register with factory
from core.component_factory import ComponentFactory
ComponentFactory.register_tool('web_search', WebSearchTool)