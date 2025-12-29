#!/usr/bin/env python3
"""
Google Sheets to SerpAPI Drone Detection Script

This script reads electric cooperative names from a Google Sheet,
searches for drone-related usage via SerpAPI, and writes results
back to the sheet.
"""

import os
import time
from typing import Dict, List, Tuple, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import requests


# ============================================================================
# Configuration (from environment variables)
# ============================================================================

GOOGLE_CREDS_PATH = os.environ.get("GOOGLE_CREDS_PATH")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SHEET_NAME = os.environ.get("SHEET_NAME", "Main")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

# Optional flags
SKIP_EXISTING = os.environ.get("SKIP_EXISTING", "False").lower() == "true"
MAX_ROWS = int(os.environ.get("MAX_ROWS", "0"))  # 0 means process all rows
MAX_NEW_ROWS = int(os.environ.get("MAX_NEW_ROWS", "0"))  # 0 means no limit on new rows processed
SERPAPI_DELAY = float(os.environ.get("SERPAPI_DELAY", "1.0"))  # seconds between calls


# ============================================================================
# Google Sheets Functions
# ============================================================================

def get_sheet():
    """
    Authenticate using OAuth 2.0 and return the worksheet object.
    
    On first run, this will open a browser for user consent.
    Subsequent runs will use the saved token.
    
    Returns:
        gspread.Worksheet: The worksheet object
    """
    if not GOOGLE_CREDS_PATH:
        raise ValueError("GOOGLE_CREDS_PATH environment variable not set")
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID environment variable not set")
    
    # OAuth 2.0 scopes
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = None
    # Store token in same directory as credentials file
    creds_dir = os.path.dirname(os.path.abspath(GOOGLE_CREDS_PATH))
    token_path = os.path.join(creds_dir, 'token.pickle')
    
    # Check if we have stored credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            # Run OAuth flow - opens browser for consent
            print("Starting OAuth 2.0 flow...")
            print("A browser window will open for you to grant permissions.")
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDS_PATH, scope)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next time
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print("Credentials saved for future use.")
    
    # Create gspread client
    client = gspread.authorize(creds)
    
    # Open spreadsheet and worksheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    
    return worksheet


def ensure_uses_drones_column(ws: gspread.Worksheet) -> int:
    """
    Ensure the 'Uses_Drones' column exists in the header row.
    If it doesn't exist, append it.
    
    Args:
        ws: The worksheet object
        
    Returns:
        int: The column index (1-based) of the Uses_Drones column
    """
    header_row = ws.row_values(1)
    
    # Check if Uses_Drones column exists
    if "Uses_Drones" in header_row:
        col_index = header_row.index("Uses_Drones") + 1  # Convert to 1-based
        print(f"Found existing 'Uses_Drones' column at column {col_index}")
        return col_index
    else:
        # Append new column - ensure sheet has enough columns
        col_index = len(header_row) + 1
        current_cols = ws.col_count
        
        # Resize sheet if needed to accommodate new column
        if col_index > current_cols:
            ws.resize(rows=ws.row_count, cols=col_index)
        
        ws.update_cell(1, col_index, "Uses_Drones")
        print(f"Added 'Uses_Drones' column at column {col_index}")
        return col_index


def ensure_drone_source_url_column(ws: gspread.Worksheet) -> int:
    """
    Ensure the 'Drone_Source_URL' column exists in the header row.
    If it doesn't exist, append it.
    
    Args:
        ws: The worksheet object
        
    Returns:
        int: The column index (1-based) of the Drone_Source_URL column
    """
    header_row = ws.row_values(1)
    
    # Check if Drone_Source_URL column exists
    if "Drone_Source_URL" in header_row:
        col_index = header_row.index("Drone_Source_URL") + 1  # Convert to 1-based
        print(f"Found existing 'Drone_Source_URL' column at column {col_index}")
        return col_index
    else:
        # Append new column - ensure sheet has enough columns
        col_index = len(header_row) + 1
        current_cols = ws.col_count
        
        # Resize sheet if needed to accommodate new column
        if col_index > current_cols:
            ws.resize(rows=ws.row_count, cols=col_index)
        
        ws.update_cell(1, col_index, "Drone_Source_URL")
        print(f"Added 'Drone_Source_URL' column at column {col_index}")
        return col_index


def fetch_rows(ws: gspread.Worksheet) -> List[Dict]:
    """
    Fetch all data rows from the worksheet.
    
    Assumes:
    - Row 1 is the header
    - Data starts at row 2
    - There is a 'Name' column
    
    Args:
        ws: The worksheet object
        
    Returns:
        List[Dict]: List of row dictionaries with keys: 'row_index', 'name', 'uses_drones_col', 'source_url_col'
    """
    # Get all values
    all_values = ws.get_all_values()
    
    if len(all_values) < 2:
        print("No data rows found (only header row exists)")
        return []
    
    # Find column indices
    header = all_values[0]
    try:
        name_col_index = header.index("Name") + 1  # Convert to 1-based
    except ValueError:
        raise ValueError("'Name' column not found in header row")
    
    uses_drones_col_index = ensure_uses_drones_column(ws)
    source_url_col_index = ensure_drone_source_url_column(ws)
    
    # Build row data
    rows = []
    for i in range(1, len(all_values)):  # Skip header row
        row_data = all_values[i]
        name = row_data[name_col_index - 1] if len(row_data) >= name_col_index else ""
        
        # Skip empty names
        if not name or not name.strip():
            continue
        
        # Get existing Uses_Drones value if present
        existing_value = None
        has_any_value = False
        if len(row_data) >= uses_drones_col_index:
            existing_val_str = row_data[uses_drones_col_index - 1].strip()
            if existing_val_str:  # If cell has any value (not empty)
                has_any_value = True
                existing_val_upper = existing_val_str.upper()
                if existing_val_upper in ("TRUE", "FALSE"):
                    existing_value = existing_val_upper == "TRUE"
                # If cell has value but not TRUE/FALSE, has_any_value=True will cause it to be skipped
        
        rows.append({
            "row_index": i + 1,  # 1-based row index in sheet
            "name": name.strip(),
            "uses_drones_col": uses_drones_col_index,
            "source_url_col": source_url_col_index,
            "existing_value": existing_value,
            "has_any_value": has_any_value
        })
    
    return rows


# ============================================================================
# SerpAPI Functions
# ============================================================================

def query_serpapi(name: str) -> Optional[Dict]:
    """
    Query SerpAPI for the utility name with drone-related keywords.
    Focuses on power line and utility inspection context.
    
    Args:
        name: The utility/cooperative name
        
    Returns:
        Dict: The JSON response from SerpAPI, or None if request failed
    """
    if not SERPAPI_API_KEY:
        raise ValueError("SERPAPI_API_KEY environment variable not set")
    
    # Build more specific query focusing on inspections
    query = f'"{name}" (drone OR UAV OR UAS OR aerial OR drones) (inspect OR inspection)'
    
    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "q": query,
        "num": 20,
        "hl": "en"
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: SerpAPI request failed: {e}")
        return None


def utility_uses_drones(serpapi_response: Dict, utility_name: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if a utility uses drones for power line inspections.
    Requires utility name (or variation), drone keywords, AND utility inspection context.
    Also returns the URL of the first relevant result.
    
    Logic:
    1. If no organic_results, return (False, None)
    2. Check each result for utility name (with abbreviation matching)
    3. Must have BOTH drone keywords AND context keywords
    4. Return (True, url) if valid match found, (False, None) otherwise
    
    Args:
        serpapi_response: The JSON response from SerpAPI
        utility_name: The name of the utility/cooperative
        
    Returns:
        Tuple[bool, Optional[str]]: (True/False, source_url or None)
    """
    if not serpapi_response:
        return (False, None)
    
    # Get organic results
    organic_results = serpapi_response.get("organic_results", [])
    
    if not organic_results:
        return (False, None)
    
    # Primary keywords (drone-related)
    drone_keywords = ["uas", "uav", "drone", "unmanned aerial vehicle", "unmanned aerial"]
    
    # Context keywords (power line/utility inspection related)
    context_keywords = [
        "power line", "transmission line", "distribution line",
        "utility inspection", "line inspection", "infrastructure inspection",
        "electrical inspection", "grid inspection", "pole inspection",
        "transmission", "distribution", "electrical grid"
    ]
    
    # Generate utility name variations for fuzzy matching
    def get_utility_name_variations(name: str) -> List[str]:
        """Generate variations of utility name to handle abbreviations."""
        name_lower = name.lower().strip()
        variations = [name_lower]  # Original name
        
        # Handle common abbreviations
        # Co-op / Cooperative
        if "co-op" in name_lower:
            variations.append(name_lower.replace("co-op", "cooperative"))
            variations.append(name_lower.replace("co-op", "co-op"))
        if "cooperative" in name_lower:
            variations.append(name_lower.replace("cooperative", "co-op"))
        
        # Assn / Association
        if "assn" in name_lower or "assn." in name_lower:
            variations.append(name_lower.replace("assn.", "association").replace("assn", "association"))
            variations.append(name_lower.replace("assn.", "assn").replace("association", "assn"))
        if "association" in name_lower:
            variations.append(name_lower.replace("association", "assn"))
        
        # Inc. / Incorporated
        if "inc." in name_lower or "inc" in name_lower:
            variations.append(name_lower.replace("inc.", "incorporated").replace("inc", "incorporated"))
            variations.append(name_lower.replace("inc.", "inc").replace("incorporated", "inc"))
        if "incorporated" in name_lower:
            variations.append(name_lower.replace("incorporated", "inc"))
        
        # Remove punctuation variations
        variations.append(name_lower.replace(".", "").replace(",", ""))
        
        # Get main name parts (first 2-3 words, excluding common suffixes)
        words = name_lower.split()
        # Remove common suffixes
        suffixes = ["inc", "inc.", "incorporated", "assn", "assn.", "association", 
                   "co-op", "cooperative", "co", "corp", "corp.", "corporation"]
        main_words = [w for w in words if w not in suffixes]
        if len(main_words) >= 2:
            # Add first 2-3 words as a variation
            variations.append(" ".join(main_words[:2]))
            if len(main_words) >= 3:
                variations.append(" ".join(main_words[:3]))
        
        return list(set(variations))  # Remove duplicates
    
    utility_variations = get_utility_name_variations(utility_name)
    
    # Banned domains (exclude these sources)
    banned_domains = ["ziprecruiter", "facebook"]
    
    # Banned keywords (exclude URLs containing these keywords)
    banned_keywords = [
        "careers", "career", "recruiting", "recruiter", "recruitment",
        "jobs", "job-board", "jobboard", "hiring", "indeed", "monster",
        "glassdoor", "linkedin.com/jobs", "simplyhired", "dice.com"
    ]
    
    # Collect all valid matches with priority scoring
    valid_matches = []
    
    for result in organic_results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        
        # Skip banned domains and careers/recruiting sites
        link_lower = link.lower()
        if any(banned in link_lower for banned in banned_domains):
            continue
        if any(keyword in link_lower for keyword in banned_keywords):
            continue
        
        text_blob = f"{title} {snippet}".lower()
        
        # MUST have utility name (or variation) in the result
        # Be strict: prefer longer, more specific matches
        has_utility_name = False
        
        # First, try full name variations (most specific)
        full_name_variations = [v for v in utility_variations if len(v.split()) >= 3]
        if full_name_variations:
            has_utility_name = any(variation in text_blob for variation in full_name_variations)
        
        # If no full name match, try at least 3-word variations
        if not has_utility_name:
            three_word_variations = [v for v in utility_variations if len(v.split()) >= 3]
            if three_word_variations:
                has_utility_name = any(variation in text_blob for variation in three_word_variations)
        
        # Only use 2-word variations if utility name is very short overall
        # (e.g., if full name is only 2 words, then 2-word match is acceptable)
        if not has_utility_name:
            utility_word_count = len(utility_name.split())
            if utility_word_count <= 3:  # If utility name is 3 words or less
                two_word_variations = [v for v in utility_variations if len(v.split()) == 2]
                if two_word_variations:
                    # Additional check: ensure the two words are significant (not common words)
                    significant_words = ["electric", "power", "energy", "cooperative", "utility", 
                                       "association", "district", "service", "authority"]
                    for variation in two_word_variations:
                        words = variation.split()
                        # Accept if variation contains significant words
                        if any(word in significant_words for word in words):
                            if variation in text_blob:
                                has_utility_name = True
                break
        
        if not has_utility_name:
            continue
        
        # Must have drone keyword
        has_drone = any(keyword in text_blob for keyword in drone_keywords)
        if not has_drone:
            continue
        
        # Must have context keyword (power line/utility inspection)
        has_context = any(context in text_blob for context in context_keywords)
        if not has_context:
            continue
        
        # Store match (no priority scoring)
        valid_matches.append(link)
    
    # If we have matches, return all unique URLs
    if valid_matches:
        # Get unique URLs while preserving order
        seen = set()
        unique_urls = []
        for link in valid_matches:
            if link not in seen:
                seen.add(link)
                unique_urls.append(link)
        
        # Return all URLs as semicolon-separated string
        all_urls = "; ".join(unique_urls)
        return (True, all_urls)
    
    # No valid matches found
    return (False, None)


# ============================================================================
# Update Functions
# ============================================================================

def update_uses_drones(ws: gspread.Worksheet, row_updates: List[Tuple[int, bool, int, Optional[str], int]]):
    """
    Update the Uses_Drones and Drone_Source_URL columns for multiple rows.
    
    Args:
        ws: The worksheet object
        row_updates: List of tuples (row_index, uses_drones, uses_drones_col, source_url, source_url_col)
    """
    if not row_updates:
        return
    
    # Helper function to convert row/col to A1 notation
    def rowcol_to_a1(row: int, col: int) -> str:
        """Convert 1-based row/col to A1 notation."""
        col_letters = ""
        while col > 0:
            col -= 1
            col_letters = chr(65 + (col % 26)) + col_letters
            col //= 26
        return f"{col_letters}{row}"
    
    # Batch update using batch_update for better performance
    updates = []
    for row_index, uses_drones, uses_drones_col, source_url, source_url_col in row_updates:
        # Update Uses_Drones column
        cell_value = "TRUE" if uses_drones else "FALSE"
        cell_a1 = rowcol_to_a1(row_index, uses_drones_col)
        updates.append({
            "range": cell_a1,
            "values": [[cell_value]]
        })
        
        # Update Drone_Source_URL column
        url_value = source_url if source_url else ""
        url_cell_a1 = rowcol_to_a1(row_index, source_url_col)
        updates.append({
            "range": url_cell_a1,
            "values": [[url_value]]
        })
    
    # Use batch_update for efficiency
    ws.batch_update(updates)


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("Google Sheets to SerpAPI Drone Detection Script")
    print("=" * 60)
    print()
    
    # Validate configuration
    missing_vars = []
    if not GOOGLE_CREDS_PATH:
        missing_vars.append("GOOGLE_CREDS_PATH")
    if not SPREADSHEET_ID:
        missing_vars.append("SPREADSHEET_ID")
    if not SERPAPI_API_KEY:
        missing_vars.append("SERPAPI_API_KEY")
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return
    
    print(f"Configuration:")
    print(f"  Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"  Sheet Name: {SHEET_NAME}")
    print(f"  Skip Existing: {SKIP_EXISTING}")
    print(f"  Max Rows: {MAX_ROWS if MAX_ROWS > 0 else 'All'}")
    print(f"  Max New Rows: {MAX_NEW_ROWS if MAX_NEW_ROWS > 0 else 'All'}")
    print(f"  SerpAPI Delay: {SERPAPI_DELAY}s")
    print()
    
    try:
        # Get worksheet
        print("Connecting to Google Sheets...")
        ws = get_sheet()
        print("Connected successfully!")
        print()
        
        # Fetch rows
        print("Fetching rows from sheet...")
        rows = fetch_rows(ws)
        total_rows = len(rows)
        print(f"Found {total_rows} rows with names")
        print()
        
        if total_rows == 0:
            print("No rows to process. Exiting.")
            return
        
        # Apply MAX_ROWS limit if set
        if MAX_ROWS > 0:
            rows = rows[:MAX_ROWS]
            print(f"Limiting to first {MAX_ROWS} rows")
            print()
        
        # Process rows
        updates = []
        processed_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        new_rows_processed = 0  # Track new rows processed (not skipped)
        
        print("Processing rows...")
        if MAX_NEW_ROWS > 0:
            print(f"Will process up to {MAX_NEW_ROWS} new rows (skipping existing values)")
        print("-" * 60)
        
        for i, row_data in enumerate(rows, 1):
            row_index = row_data["row_index"]
            name = row_data["name"]
            uses_drones_col = row_data["uses_drones_col"]
            source_url_col = row_data["source_url_col"]
            existing_value = row_data["existing_value"]
            
            print(f"[{i}/{len(rows)}] Row {row_index}: {name}")
            
            # Skip if already has value and SKIP_EXISTING is True
            # Skip if cell has TRUE/FALSE value OR if cell has any non-empty value
            has_any_value = row_data.get("has_any_value", False)
            if SKIP_EXISTING and (existing_value is not None or has_any_value):
                value_display = existing_value if existing_value is not None else "non-empty"
                print(f"  SKIPPED: Already has value ({value_display})")
                skipped_count += 1
                continue
            
            # Check if we've reached MAX_NEW_ROWS limit
            if MAX_NEW_ROWS > 0 and new_rows_processed >= MAX_NEW_ROWS:
                print(f"\nReached MAX_NEW_ROWS limit ({MAX_NEW_ROWS}). Stopping.")
                break
            
            # Query SerpAPI
            print(f"  Querying SerpAPI...")
            response = query_serpapi(name)
            
            if response is None:
                print(f"  ERROR: Failed to get SerpAPI response")
                error_count += 1
                processed_count += 1
                time.sleep(SERPAPI_DELAY)
                continue
            
            # Determine if uses drones and get source URL
            uses_drones, source_url = utility_uses_drones(response, name)
            print(f"  Result: {'TRUE' if uses_drones else 'FALSE'}")
            if source_url:
                print(f"  Source: {source_url}")
            
            # Queue update (row_index, uses_drones, uses_drones_col, source_url, source_url_col)
            updates.append((row_index, uses_drones, uses_drones_col, source_url, source_url_col))
            updated_count += 1
            processed_count += 1
            new_rows_processed += 1  # Increment counter for new rows processed
            
            # Rate limiting
            if i < len(rows):  # Don't sleep after last row
                time.sleep(SERPAPI_DELAY)
        
        print("-" * 60)
        print()
        
        # Write updates to sheet
        if updates:
            print(f"Writing {len(updates)} updates to Google Sheets...")
            update_uses_drones(ws, updates)
            print("Updates written successfully!")
            print()
        
        # Summary
        print("=" * 60)
        print("Summary:")
        print(f"  Total rows found: {total_rows}")
        print(f"  Rows processed: {processed_count}")
        print(f"  Rows updated: {updated_count}")
        print(f"  Rows skipped: {skipped_count}")
        print(f"  Errors: {error_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
