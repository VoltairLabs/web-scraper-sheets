# Web Scraper to Google Sheets Automation

A Python project for scraping web data and automatically updating Google Sheets.

## Setup

### Quick Setup (Recommended)

Run the automated setup script:
```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Guide you through next steps

### Manual Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Google Sheets API Setup:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Drive API
   - Create OAuth 2.0 Client ID credentials (Desktop app type)
   - Download credentials JSON file

4. **Set environment variables:**
   ```bash
   source setup_env.sh
   ```
   Or set them manually:
   ```bash
   export GOOGLE_CREDS_PATH="/path/to/your/oauth-credentials.json"
   export SPREADSHEET_ID="your-spreadsheet-id"
   export SHEET_NAME="Main"
   export SERPAPI_API_KEY="your-serpapi-key"
   ```

5. **Run the script:**
   ```bash
   python main.py
   ```

### Daily Usage

After initial setup:
```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
source setup_env.sh

# Run the script
python main.py

# Deactivate when done (optional)
deactivate
```

## Project Structure

```
web-scraper-sheets/
├── main.py              # Main scraper script
├── scraper.py           # Web scraping logic
├── sheets_handler.py    # Google Sheets integration
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Usage

More specific instructions will be added based on your requirements.

