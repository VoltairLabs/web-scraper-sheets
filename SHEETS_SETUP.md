# Google Sheets Integration Setup

This guide explains how to set up Google Sheets API access for the `sheets_scraper.py` script using OAuth2.

## OAuth2 Setup

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Sheets API and Google Drive API**:
   - Go to [API Library](https://console.cloud.google.com/apis/library)
   - Search for "Google Sheets API" and enable it
   - Search for "Google Drive API" and enable it

3. **Create OAuth2 Credentials**:
   - Go to [Credentials](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure the OAuth consent screen:
     - Choose "External" (unless you have a Google Workspace account)
     - Fill in the required fields (App name, User support email, Developer contact)
     - Add scopes: `https://www.googleapis.com/auth/spreadsheets` and `https://www.googleapis.com/auth/drive`
     - Add test users if needed (for testing phase)
     - Save and continue
   - Back at Credentials, click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Give it a name (e.g., "Sheets Scraper")
   - Click "Create"
   - Download the JSON file
   - Save it as `credentials.json` in this directory (or note the path)

4. **Run the script for the first time**:
   ```bash
   python sheets_scraper.py --credentials credentials.json --limit 10
   ```
   
   - On first run, it will open a browser window for you to authorize the application
   - Sign in with your Google account
   - Grant permissions to access Google Sheets
   - The authorization token will be saved to `token.pickle` for future runs
   - You won't need to authorize again unless the token expires

5. **Subsequent runs**:
   ```bash
   python sheets_scraper.py --credentials credentials.json
   ```
   
   The script will use the saved token automatically.

## Environment Variables (Optional)

Instead of using `--credentials`, you can set:
```bash
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
python sheets_scraper.py
```

## Quick Start

Once you have credentials set up:

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Make sure your SERPAPI_KEY is set
export SERPAPI_KEY=your_key_here

# Run the scraper (uses default sheet ID and gid from the script)
python sheets_scraper.py --credentials credentials.json --limit 10
```

**Note:** Make sure your virtual environment is activated before running any scripts!

## Command Line Options

```bash
python sheets_scraper.py --help
```

Options:
- `--sheet-id`: Google Sheet ID (default: from your URL)
- `--gid`: Google Sheet tab/gid (default: from your URL)
- `--credentials`: Path to OAuth2 client credentials JSON file (required)
- `--token`: Path to OAuth2 token file (default: token.pickle)
- `--serpapi-key`: SerpAPI key (optional, can use SERPAPI_KEY env var)
- `--limit`: Limit number of utilities to check (useful for testing)

## Troubleshooting

- **"Credentials file not found"**: Make sure you downloaded the OAuth2 client credentials JSON file and specified the correct path
- **Token expired**: Delete `token.pickle` and run again to re-authorize
- **Permission denied**: Make sure the Google account you authorize has access to the Google Sheet
