"""Web scraping module."""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebScraper:
    """Base web scraper class."""
    
    def __init__(self, url: str, headers: Optional[Dict] = None):
        """
        Initialize the web scraper.
        
        Args:
            url: The URL to scrape
            headers: Optional HTTP headers
        """
        self.url = url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_page(self) -> Optional[BeautifulSoup]:
        """
        Fetch and parse the web page.
        
        Returns:
            BeautifulSoup object or None if request fails
        """
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return None
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method. Override this in subclasses.
        
        Returns:
            List of dictionaries containing scraped data
        """
        soup = self.fetch_page()
        if not soup:
            return []
        
        # Override this method with your specific scraping logic
        return []
    
    def extract_text(self, element) -> str:
        """Extract text from a BeautifulSoup element."""
        return element.get_text(strip=True) if element else ''


class SeleniumScraper:
    """Selenium-based scraper for JavaScript-rendered pages."""
    
    def __init__(self, url: str, driver_path: Optional[str] = None, headless: bool = True):
        """
        Initialize the Selenium scraper.
        
        Args:
            url: The URL to scrape
            driver_path: Path to ChromeDriver
            headless: Run browser in headless mode
        """
        self.url = url
        self.driver_path = driver_path
        self.headless = headless
        self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if self.driver_path:
            self.driver = webdriver.Chrome(executable_path=self.driver_path, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.driver:
            self.driver.quit()
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method. Override this in subclasses.
        
        Returns:
            List of dictionaries containing scraped data
        """
        if not self.driver:
            return []
        
        self.driver.get(self.url)
        # Override this method with your specific scraping logic
        return []

