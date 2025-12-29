# Web Scraper using SerpAPI

A Python web scraper for extracting Google search results using SerpAPI.

## Scripts

- **`scraper.py`** - General-purpose Google search scraper using SerpAPI
- **`sheets_scraper.py`** - Google Sheets integration that checks utilities for satellite data usage
- **`sheets_scraper_pano.py`** - Google Sheets integration that checks utilities for Pano AI camera usage

For Google Sheets integration setup, see [SHEETS_SETUP.md](SHEETS_SETUP.md).

## Quick Start - Test Google Sheets Scraper on First 10 Rows

To test the Google Sheets scraper on the first 10 utilities:

```bash
# Activate virtual environment
source venv/bin/activate

# Set SerpAPI key (or use .env file)
export SERPAPI_KEY=your_serpapi_key_here

# Run on first 10 rows
python sheets_scraper.py --credentials credentials.json --limit 10
```

**Or use environment variable for credentials:**
```bash
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
export SERPAPI_KEY=your_serpapi_key_here
python sheets_scraper.py --limit 10
```

**What it does:**
- Searches for each utility name with the following requirements:
  - Utility name (with variations: Cooperative/Coop/Co-op, Company/Co/Co., Corporation/Corp/Corp.)
  - AND ("satellite" OR "overstory" OR "AiDash" OR "ai") - case-insensitive
  - AND ("vegetation" OR "right-of-way" OR "ROW" OR "right of way") - case-insensitive
- Validates that all three conditions appear in the page content (title/snippet) - case-insensitive matching
- **Excludes certain sources:**
  - Facebook URLs (facebook.com)
  - Pages containing "satellite dish" or related phrases (satellite dishes, dish satellite, tv satellite dish, satellite internet, satellite campus, satellite facility, overstory trees, satellite box, satellite boxes)
  - Pages containing "cable", "broadband", "campus", "iecl", "issuu", or "indianaconnection"
- Checks Google Sheets column A for utility names
- Updates "Using Satellite" column with True/False
- Updates "Source" column with matching URLs
- Only processes first 10 utilities when using `--limit 10`

**Note:** Make sure you have:
1. Set up OAuth2 credentials (see [SHEETS_SETUP.md](SHEETS_SETUP.md))
2. Set your SerpAPI key in the environment or pass it via `--serpapi-key`
3. The Google Sheet is accessible with your OAuth2 account

## Quick Start - Pano AI Scraper

To check utilities for Pano AI camera usage:

```bash
# Activate virtual environment
source venv/bin/activate

# Run on first 10 rows (for testing)
python sheets_scraper_pano.py --credentials credentials.json --limit 10
```

**Or use environment variable for credentials:**
```bash
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
export SERPAPI_KEY=your_serpapi_key_here
python sheets_scraper_pano.py --limit 10
```

**What it does:**
- Searches for each utility name with the following requirements:
  - Utility name (with variations: Cooperative/Coop/Co-op, Company/Co/Co., Corporation/Corp/Corp.)
  - AND ("pano ai" OR "panoai" OR "ai camera" OR "panoramic ai camera" OR "pano camera" OR "panoramic camera") - case-insensitive
- Validates that both utility name and Pano AI keyword appear in the page content (title/snippet) - case-insensitive matching
- Checks Google Sheets column A for utility names
- Updates "Using Pano AI" column with True/False
- Updates "Pano AI Source" column with matching URLs
- Only processes first 10 utilities when using `--limit 10`
- Automatically resumes from the first empty row in "Using Pano AI" column

## Features

- 🔍 Search Google
- 📊 Extract organic search results (title, link, snippet)
- 💾 Save results to JSON
- 🎯 Configurable number of results and location
- 🔐 Secure API key management via environment variables

## Installation

1. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your SerpAPI key (choose one method):

   **Option A: Use setup script (recommended for local development)**
   ```bash
   source setup_env.sh
   ```
   
   **Option B: Create .env file (automatically loaded by python-dotenv)**
   ```bash
   cp env.template .env
   # Edit .env and add your API key: SERPAPI_KEY=your_key_here
   ```
   
   **Option C: Export environment variable manually**
   ```bash
   export SERPAPI_KEY=your_actual_api_key_here
   ```
   
   **Option D: Pass as command-line argument**
   ```bash
   python scraper.py "query" --api-key your_key_here
   ```

   Note: The scraper automatically loads from `.env` file if python-dotenv is installed.

## Usage

**Note:** Make sure your virtual environment is activated before running scripts!

### Command Line

Basic search:
```bash
python scraper.py "python web scraping"
```

Get more results:
```bash
python scraper.py "python web scraping" --num 20
```

Save to specific file:
```bash
python scraper.py "python web scraping" --output my_results.json
```

Search from specific location:
```bash
python scraper.py "restaurants" --location "New York, New York, United States"
```

### Python API

```python
from scraper import WebScraper
import os

# Initialize scraper (reads SERPAPI_KEY from environment)
scraper = WebScraper()

# Search Google
results = scraper.search_google("python tutorials", num_results=10)

# Extract organic results
organic = scraper.extract_organic_results(results)

# Print results
scraper.print_results(organic)

# Save to file
scraper.save_results(organic, "output.json")
```

## Example Output

The scraper extracts:
- **Title**: Page title
- **Link**: URL
- **Snippet**: Description/preview text

Results are saved in JSON format:
```json
[
  {
    "title": "Example Result Title",
    "link": "https://example.com",
    "snippet": "This is a description of the result..."
  }
]
```

## Requirements

- Python 3.7+
- SerpAPI account and API key
- `google-search-results` package (installed via requirements.txt)

## API Key

Sign up at [SerpAPI](https://serpapi.com/) to get your free API key. The free tier includes 100 searches per month.

## License

MIT

