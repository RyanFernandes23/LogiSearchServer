from bs4 import BeautifulSoup
import requests
from duckduckgo_search import DDGS
from typing import Optional, List, Dict, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.3'
}

def scrape_website(url: str, headers: Optional[dict] = None, timeout: int = 10) -> BeautifulSoup:
    """
    Scrape a website with robust error handling and safety measures.
    
    Args:
        url: Website URL to scrape
        headers: Custom headers (defaults to Chrome user agent)
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        BeautifulSoup object parsed from the HTML content
    
    Raises:
        ValueError: For invalid URL or failed request
    """
    try:
        response = requests.get(
            url,
            headers=headers or DEFAULT_HEADERS,
            timeout=timeout,
            verify=True  # Enable SSL verification
        )
        response.raise_for_status()
        
        if not response.content:
            raise ValueError(f"Empty response from {url}")
            
        return BeautifulSoup(response.content, 'lxml')
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        raise ValueError(f"Failed to fetch {url}: {str(e)}") from e

def extract_elements(
    soup: BeautifulSoup,
    element_type: str,
    class_name: Optional[str] = None,
    id_name: Optional[str] = None,
    **kwargs
) -> list:
    """
    Flexible element extraction with CSS selector support.
    
    Args:
        soup: BeautifulSoup object
        element_type: HTML element type (div, p, etc.)
        class_name: CSS class filter
        id_name: Element ID filter
        kwargs: Additional attributes for filtering
    
    Returns:
        List of matching elements
    """
    try:
        css_selector = element_type
        
        if class_name:
            css_selector += f'.{class_name.replace(" ", ".")}'
        if id_name:
            css_selector += f'#{id_name}'
        
        # Handle additional attributes
        attr_selectors = [f'[{k}="{v}"]' for k, v in kwargs.items()]
        css_selector += ''.join(attr_selectors)
        
        return soup.select(css_selector)
    except Exception as e:
        logger.error(f"Element extraction failed: {str(e)}")
        return []

def search_text(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """
    Safe and configurable text search with error handling.
    
    Args:
        query: Search query string
        max_results: Number of results to return (1-20)
    
    Returns:
        List of search result dictionaries
    """
    try:
        # Validate input parameters
        max_results = max(1, min(20, max_results))  # Keep within 1-20 range
        
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results,safesearch="moderate"))
    
    except Exception as e:
        logger.error(f"Search failed for '{query}': {str(e)}")
        return []

if __name__ == "__main__":
    # Example usage
    try:
        query = "latest advancements in artificial intelligence"
        results = search_text(query)
        logger.info(f"Search results: {results}")
        
        if results:
            first_url = results[0]['href']
            soup = scrape_website(first_url)
            articles = extract_elements(soup, 'article', class_name='post')
            logger.info(f"Found {len(articles)} articles on {first_url}")
            
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")