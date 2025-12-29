#!/usr/bin/env python3
"""
Web Scraper using SerpAPI
Scrapes Google search engine results
"""

import os
import json
import sys
from typing import Dict, List, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will rely on environment variables

from serpapi import GoogleSearch


class WebScraper:
    """Web scraper using SerpAPI for search engine results"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the scraper with SerpAPI key
        
        Args:
            api_key: SerpAPI key (if None, reads from SERPAPI_KEY env var)
        """
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError(
                "SerpAPI key required. Set SERPAPI_KEY environment variable "
                "or pass api_key parameter"
            )
    
    def search_google(
        self,
        query: str,
        num_results: int = 10,
        location: str = "United States",
        **kwargs
    ) -> Dict:
        """
        Search Google using SerpAPI
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
            location: Location for search (default: "United States")
            **kwargs: Additional search parameters
        
        Returns:
            Dictionary containing search results
        """
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "location": location,
            **kwargs
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            print(f"Error searching Google: {e}", file=sys.stderr)
            raise
    
    def extract_organic_results(self, results: Dict) -> List[Dict]:
        """
        Extract organic search results from API response
        
        Args:
            results: Raw results from SerpAPI
        
        Returns:
            List of dictionaries containing title, link, and snippet
        """
        organic_results = []
        results_list = results.get("organic_results", [])
        
        for result in results_list:
            organic_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        
        return organic_results
    
    def save_results(self, results: List[Dict], filename: str = "results.json"):
        """
        Save results to a JSON file
        
        Args:
            results: List of result dictionaries
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_results(self, results: List[Dict]):
        """
        Print results to console
        
        Args:
            results: List of result dictionaries
        """
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('link', 'No link')}")
            print(f"   {result.get('snippet', 'No snippet')}")


def main():
    """Example usage of the WebScraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web Scraper using SerpAPI")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--location",
        default="United States",
        help="Location for search (default: United States)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file (optional)"
    )
    parser.add_argument(
        "--api-key",
        help="SerpAPI key (optional, can use SERPAPI_KEY env var)"
    )
    
    args = parser.parse_args()
    
    try:
        scraper = WebScraper(api_key=args.api_key)
        
        raw_results = scraper.search_google(
            args.query,
            num_results=args.num,
            location=args.location
        )
        
        organic_results = scraper.extract_organic_results(raw_results)
        
        scraper.print_results(organic_results)
        
        if args.output:
            scraper.save_results(organic_results, args.output)
        else:
            scraper.save_results(organic_results)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

