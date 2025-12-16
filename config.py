"""Configuration management for the web scraper."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Google Sheets Configuration
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Sheet1')
    CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')
    
    # Scraper Configuration
    SCRAPE_URL = os.getenv('SCRAPE_URL', '')
    SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', '3600'))
    
    # Selenium Configuration (if needed)
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '')
    HEADLESS = os.getenv('HEADLESS', 'True').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = ['GOOGLE_SHEET_ID', 'SCRAPE_URL']
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

