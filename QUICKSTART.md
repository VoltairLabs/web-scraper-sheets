# Quick Start Guide

## 🚀 Initial Setup

### Step 1: Set Up Virtual Environment

**Option A: Automated Setup (Recommended)**
```bash
./setup.sh
```

**Option B: Manual Setup**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Activate Virtual Environment

After setup, always activate the virtual environment before running:
```bash
source venv/bin/activate
```

You'll see `(venv)` in your terminal prompt when it's active.

## ✅ Already Configured

The following values have been set up for you:

- **Spreadsheet ID**: `1E5-i7-MacB5MfYfs_do_fGD7-NFYGcU_tft-Ab-pPRg`
- **Sheet Name**: `Main`
- **SerpAPI API Key**: `8821c01916831cf0a1a3c075f3043bf085496c07332e778934e67c622be8c98a`
- **Google Credentials Path**: `/Users/avigotskind/Downloads/GD API.json`

## ⚠️ Still Needed: Google OAuth 2.0 Client ID Credentials

You need to set up OAuth 2.0 credentials to access your Google Sheet.

### Steps:

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create or select a project**

3. **Enable APIs**:
   - Go to "APIs & Services" → "Library"
   - Enable "Google Sheets API"
   - Enable "Google Drive API"

4. **Create OAuth 2.0 Client ID**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" user type (unless you have a Google Workspace)
     - Fill in app name, user support email, developer contact
     - Add scopes: `https://www.googleapis.com/auth/spreadsheets` and `https://www.googleapis.com/auth/drive`
     - Add your email as a test user
     - Save and continue
   - For Application type, choose "Desktop app"
   - Give it a name (e.g., "Sheets Drone Scraper")
   - Click "Create"
   - Download the JSON file
   - Save it somewhere safe (e.g., `~/credentials/oauth-credentials.json`)

5. **Note**: The script will use your Google account to access the sheet. Make sure you have edit access to the Google Sheet you want to modify.

## 🚀 Running the Script

**Important**: Always activate the virtual environment first!

```bash
# Activate virtual environment
source venv/bin/activate
```

### Option 1: Using the setup script (Recommended)

```bash
# 1. Activate virtual environment (if not already active)
source venv/bin/activate

# 2. Source the setup script (sets all environment variables)
source setup_env.sh

# 3. Run the script (first time will open browser for consent)
python main.py
```

**First Run**: A browser window will open asking you to sign in and grant permissions. After you approve, the script will save a token for future use.

**Subsequent Runs**: The script will use the saved token automatically (no browser needed).

### Option 2: Using environment variables directly

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export GOOGLE_CREDS_PATH="/path/to/your/oauth-credentials.json"
export SPREADSHEET_ID="1E5-i7-MacB5MfYfs_do_fGD7-NFYGcU_tft-Ab-pPRg"
export SHEET_NAME="Main"
export SERPAPI_API_KEY="8821c01916831cf0a1a3c075f3043bf085496c07332e778934e67c622be8c98a"

# Run the script
python main.py
```

### Option 3: Using a .env file

1. Create a `.env` file in this directory:
```
GOOGLE_CREDS_PATH=/path/to/your/oauth-credentials.json
SPREADSHEET_ID=1E5-i7-MacB5MfYfs_do_fGD7-NFYGcU_tft-Ab-pPRg
SHEET_NAME=Main
SERPAPI_API_KEY=8821c01916831cf0a1a3c075f3043bf085496c07332e778934e67c622be8c98a
```

2. Activate virtual environment and run:
```bash
source venv/bin/activate
python main.py
```

Note: The script will automatically load `.env` if `python-dotenv` is installed.

## 📋 Google Sheet Requirements

Your Google Sheet should have:
- A header row in row 1
- A column named `Name` (case-sensitive) containing utility/cooperative names
- Data rows starting from row 2

The script will automatically:
- Create a `Uses_Drones` column if it doesn't exist
- Fill it with `TRUE` or `FALSE` based on search results

## 🧪 Testing

To test with just a few rows first:

```bash
source venv/bin/activate
source setup_env.sh
export MAX_ROWS=5  # Process only first 5 rows
python main.py
```

## 📊 Optional Settings

- `SKIP_EXISTING=True` - Skip rows that already have TRUE/FALSE values
- `MAX_ROWS=10` - Limit processing to first N rows
- `SERPAPI_DELAY=2.0` - Delay between API calls (default: 1.0 seconds)

Example:
```bash
source venv/bin/activate
export SKIP_EXISTING=True
export MAX_ROWS=10
source setup_env.sh
python main.py
```

## 🔄 Daily Workflow

Once everything is set up, your daily workflow is simple:

```bash
# 1. Navigate to project directory
cd /Users/avigotskind/web-scraper-sheets

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set environment variables
source setup_env.sh

# 4. Run the script
python main.py

# 5. (Optional) Deactivate when done
deactivate
```

**Pro Tip**: You can create an alias in your `~/.zshrc` or `~/.bashrc`:
```bash
alias run-drone-scraper='cd /Users/avigotskind/web-scraper-sheets && source venv/bin/activate && source setup_env.sh && python main.py'
```

Then just run: `run-drone-scraper`

