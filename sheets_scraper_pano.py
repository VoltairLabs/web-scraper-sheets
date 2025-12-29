#!/usr/bin/env python3
"""
Google Sheets Scraper - Pano AI
Checks if utilities are using Pano AI cameras for inspections
"""

import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from serpapi import GoogleSearch


class SheetsPanoAIChecker:
    """Checks utilities in Google Sheets for Pano AI camera usage"""
    
    # Google Sheets scopes
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    def __init__(
        self,
        sheet_id: str,
        serpapi_key: Optional[str] = None,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        """
        Initialize the checker
        
        Args:
            sheet_id: Google Sheet ID
            serpapi_key: SerpAPI key (if None, reads from SERPAPI_KEY env var)
            credentials_path: Path to OAuth2 client credentials JSON file
            token_path: Path to store OAuth2 token (default: token.pickle)
        """
        self.sheet_id = sheet_id
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')
        self.token_path = token_path or 'token.pickle'
        
        if not self.serpapi_key:
            raise ValueError(
                "SerpAPI key required. Set SERPAPI_KEY environment variable "
                "or pass serpapi_key parameter"
            )
        
        # Initialize Google Sheets client with OAuth2
        if not credentials_path:
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_FILE')
        
        if not credentials_path:
            raise ValueError(
                "OAuth2 credentials file required. Set GOOGLE_CREDENTIALS_FILE "
                "environment variable or use --credentials option"
            )
        
        creds = self._get_oauth2_credentials(credentials_path)
        self.client = gspread.authorize(creds)
        self.sheet = None
    
    def _get_oauth2_credentials(self, credentials_path: str) -> Credentials:
        """
        Get OAuth2 credentials, loading from token if available or prompting for authorization
        
        Args:
            credentials_path: Path to OAuth2 client credentials JSON file
        
        Returns:
            OAuth2 Credentials object
        """
        creds = None
        
        # Load token if it exists
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Could not load token file: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Warning: Could not refresh token: {e}")
                    creds = None
            
            if not creds:
                # Get new credentials
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {credentials_path}\n"
                        f"Please download OAuth2 client credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPE
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for next time
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                print(f"✓ Token saved to {self.token_path}")
            except Exception as e:
                print(f"Warning: Could not save token: {e}")
        
        return creds
    
    def open_sheet(self, gid: Optional[str] = None):
        """Open the Google Sheet"""
        try:
            # Open the spreadsheet by ID
            self.sheet = self.client.open_by_key(self.sheet_id)
            
            if gid:
                # Try to find worksheet by gid
                for ws in self.sheet.worksheets():
                    if str(ws.id) == str(gid):
                        self.worksheet = ws
                        print(f"✓ Opened worksheet: {ws.title} (gid: {gid})")
                        return
                # If not found by gid, use first worksheet
                print(f"Warning: Worksheet with gid {gid} not found, using first worksheet")
                self.worksheet = self.sheet.sheet1
            else:
                self.worksheet = self.sheet.sheet1
                print(f"✓ Opened worksheet: {self.worksheet.title}")
        except Exception as e:
            raise ValueError(f"Failed to open Google Sheet: {e}")
    
    def find_or_create_column(self, column_name: str) -> int:
        """
        Find column or create it if it doesn't exist
        
        Args:
            column_name: Name of the column to find or create
        
        Returns:
            Column index (1-based)
        """
        # Get all values in first row (headers)
        try:
            headers = self.worksheet.row_values(1)
        except Exception as e:
            raise ValueError(f"Failed to read headers: {e}")
        
        # Check if column exists
        if column_name in headers:
            col_index = headers.index(column_name) + 1  # gspread uses 1-based indexing
            print(f"✓ Found existing column '{column_name}' at column {col_index}")
        else:
            # Try to create new column at the end
            col_index = len(headers) + 1
            try:
                self.worksheet.update_cell(1, col_index, column_name)
                print(f"✓ Created new column '{column_name}' at column {col_index}")
            except Exception as e:
                # If we're at the column limit, we need to add columns to the sheet first
                if "exceeds grid limits" in str(e) or "400" in str(e):
                    print(f"⚠️  At column limit, adding columns to sheet...")
                    try:
                        # Add columns to expand the sheet
                        current_cols = len(headers)
                        cols_to_add = 5  # Add a few columns to have room
                        self.worksheet.add_cols(cols_to_add)
                        # Now try to create the column again
                        self.worksheet.update_cell(1, col_index, column_name)
                        print(f"✓ Created new column '{column_name}' at column {col_index}")
                    except Exception as e2:
                        raise ValueError(
                            f"Could not create column '{column_name}'. "
                            f"Error: {e2}. The sheet may need manual column expansion."
                        )
                else:
                    raise
        
        return col_index
    
    def find_start_row(self, column_index: int) -> int:
        """
        Find the first row that doesn't have a value in the specified column
        
        Args:
            column_index: Column index to check (1-based)
        
        Returns:
            Starting row number (1-based)
        """
        start_row = 2  # Start from row 2 (row 1 is headers)
        try:
            # Get all values in the column
            column_values = self.worksheet.col_values(column_index)
            for i, value in enumerate(column_values[1:], start=2):  # Skip header row
                value_str = str(value).strip()
                if not value_str:  # Empty cell
                    start_row = i
                    break
            else:
                # All rows have values, start at the end
                if len(column_values) > 1:
                    start_row = len(column_values) + 1
                else:
                    start_row = 2
        except Exception as e:
            print(f"Warning: Could not read column values: {e}")
            start_row = 2
        
        return start_row
    
    def get_utilities_from_column_a(self, start_row: int = 2, limit: Optional[int] = None) -> List[Tuple[int, str]]:
        """
        Get utilities from column A starting from start_row
        
        Args:
            start_row: Row to start from (1-based)
            limit: Maximum number of utilities to return (None for all)
        
        Returns:
            List of tuples (row_number, utility_name)
        """
        utilities = []
        try:
            # Get all values in column A
            column_a_values = self.worksheet.col_values(1)
            
            # Start from the specified row
            for i in range(start_row - 1, len(column_a_values)):  # -1 because list is 0-indexed
                if limit and len(utilities) >= limit:
                    break
                    
                utility = column_a_values[i].strip()
                if utility:  # Only include non-empty values
                    utilities.append((i + 1, utility))  # +1 because gspread uses 1-based indexing
            
            print(f"✓ Found {len(utilities)} utilities to check")
            return utilities
        except Exception as e:
            raise ValueError(f"Failed to read utilities from column A: {e}")
    
    def _generate_utility_name_variations(self, utility_name: str) -> List[str]:
        """
        Generate variations of utility name to account for different formatting
        
        Examples:
        - "Flathead Electric Cooperative" -> ["Flathead Electric Cooperative", "Flathead Electric Coop", "Flathead Electric Co-op"]
        - "SECO Energy" -> ["SECO Energy"]
        
        Args:
            utility_name: Original utility name
        
        Returns:
            List of utility name variations
        """
        variations = [utility_name]  # Always include original
        
        # Generate variations for common abbreviations
        if "Cooperative" in utility_name:
            variations.append(utility_name.replace("Cooperative", "Coop"))
            variations.append(utility_name.replace("Cooperative", "Co-op"))
        
        if "Company" in utility_name:
            variations.append(utility_name.replace("Company", "Co"))
            variations.append(utility_name.replace("Company", "Co."))
        
        if "Corporation" in utility_name:
            variations.append(utility_name.replace("Corporation", "Corp"))
            variations.append(utility_name.replace("Corporation", "Corp."))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                seen.add(var)
                unique_variations.append(var)
        
        return unique_variations
    
    def check_pano_ai_usage(self, utility_name: str) -> Tuple[bool, List[str]]:
        """
        Check if utility uses Pano AI cameras for inspections
        
        Requires: utility name (any variation) AND ("pano ai" OR "panoai" OR "ai camera" OR similar)
        
        Args:
            utility_name: Name of the utility
        
        Returns:
            Tuple of (is_using_pano_ai: bool, source_urls: List[str])
        """
        # Generate utility name variations
        utility_variations = self._generate_utility_name_variations(utility_name)
        
        # Create search query with all variations
        # Format: (utility1 OR utility2 OR ...) AND ("pano ai" OR "panoai" OR "ai camera" OR ...)
        utility_terms = " OR ".join([f'"{var}"' for var in utility_variations])
        pano_terms = '"pano ai" OR "panoai" OR "ai camera" OR "ai-enabled camera" OR "ai enabled camera" OR "ai-powered camera" OR "ai powered camera" OR "ai-powered cameras" OR "ai powered cameras"'
        query = f'({utility_terms}) AND ({pano_terms})'
        
        print(f"  Checking: {utility_name}...")
        source_urls = []
        
        # Keywords that must appear (case-insensitive - all checked as lowercase)
        required_pano_keywords = ['pano ai', 'panoai', 'ai camera', 'ai-enabled camera', 'ai enabled camera', 'ai-powered camera', 'ai powered camera', 'ai-powered cameras', 'ai powered cameras']
        
        try:
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": 10,  # First page of results only (typically 10 results per page)
                "tbs": "qdr:y8",  # Filter results from the last 8 years only
            }
            
            # Wrap API call with timeout to prevent hanging (60 second timeout)
            def perform_search():
                search = GoogleSearch(params)
                return search.get_dict()
            
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(perform_search)
                    results = future.result(timeout=60)  # 60 second timeout
            except FutureTimeoutError:
                print(f"    ⚠️  Search timeout after 60 seconds, skipping...")
                return False, []
            
            organic_results = results.get("organic_results", [])
            
            # Create lowercase versions of utility name variations for matching
            utility_variations_lower = [var.lower() for var in utility_variations]
            
            # Check each result - must contain utility name (any variation) AND one of the pano keywords
            for result in organic_results:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                # Exclude banned URLs
                banned_urls = [
                    'distributech.com',
                    'chartwellinc.com',
                    'lobbylinx.com',
                    're-plus.com/see-whos-attending/'
                ]
                link_lower = link.lower()
                if any(banned_url in link_lower for banned_url in banned_urls):
                    continue
                
                # Convert to lowercase for case-insensitive matching
                title_lower = title.lower()
                snippet_lower = snippet.lower()
                page_content_lower = f"{title_lower} {snippet_lower}"
                
                # Exclude pages containing banned words
                banned_words = ['panasonic']
                if any(banned_word in page_content_lower for banned_word in banned_words):
                    continue
                
                # Check if utility name (any variation) appears as a complete phrase (case-insensitive)
                # Must appear in title or snippet - strict validation
                utility_found = False
                for var_lower in utility_variations_lower:
                    # Check if the utility name variation appears in title or snippet
                    if var_lower in title_lower or var_lower in snippet_lower:
                        utility_found = True
                        break
                
                # Check if at least one pano keyword appears (case-insensitive)
                pano_keyword_found = False
                for keyword in required_pano_keywords:
                    if keyword in page_content_lower:
                        pano_keyword_found = True
                        break
                
                # Both must be present - strict validation ensures utility name is in title/snippet
                if utility_found and pano_keyword_found:
                    if link and link not in source_urls:
                        source_urls.append(link)
            
            found_evidence = len(source_urls) > 0
            
            if found_evidence:
                print(f"    ✓ Found {len(source_urls)} source URL(s) with Pano AI information")
            else:
                print(f"    ✗ No evidence of Pano AI usage found")
            
        except Exception as e:
            print(f"    Error during search: {e}")
            return False, []
        
        return found_evidence, source_urls
    
    def update_sheet(
        self,
        results: List[Tuple[int, bool, List[str]]],
        pano_col_index: int,
        source_col_index: int
    ):
        """
        Update Google Sheet with results using batch updates
        
        Args:
            results: List of tuples (row_number, is_using_pano_ai, source_urls)
            pano_col_index: Column index for "Using Pano AI" (1-based)
            source_col_index: Column index for "Pano AI Source" (1-based)
        """
        if not results:
            print("No results to update")
            return
        
        print(f"  Batch updating {len(results)} rows...")
        
        try:
            # Get column letters from indices (A=1, B=2, etc.)
            def col_index_to_letter(col_index: int) -> str:
                """Convert 1-based column index to letter (A, B, C, etc.)"""
                result = ""
                col_idx = col_index
                while col_idx > 0:
                    col_idx -= 1
                    result = chr(col_idx % 26 + ord('A')) + result
                    col_idx //= 26
                return result
            
            pano_col = col_index_to_letter(pano_col_index)
            source_col = col_index_to_letter(source_col_index)
            
            # Prepare batch update data
            batch_updates = []
            
            for row_num, is_using_pano_ai, source_urls in results:
                # Create individual cell updates for each row
                pano_range = f"{pano_col}{row_num}"
                batch_updates.append({
                    'range': pano_range,
                    'values': [[str(is_using_pano_ai)]]
                })
                
                source_text = ", ".join(source_urls) if source_urls else ""
                source_range = f"{source_col}{row_num}"
                batch_updates.append({
                    'range': source_range,
                    'values': [[source_text]]
                })
            
            if batch_updates:
                # Execute batch update (updates all cells in one API call)
                self.worksheet.batch_update(batch_updates)
                print(f"✓ Successfully batch updated {len(results)} rows (2 columns in 1 API call)")
            else:
                print("No rows to update")
                
        except Exception as e:
            print(f"  Error during batch update: {e}")
            print("  Falling back to individual cell updates...")
            # Fallback to individual updates if batch fails
            updated = 0
            for row_num, is_using_pano_ai, source_urls in results:
                try:
                    self.worksheet.update_cell(row_num, pano_col_index, str(is_using_pano_ai))
                    source_text = ", ".join(source_urls) if source_urls else ""
                    self.worksheet.update_cell(row_num, source_col_index, source_text)
                    updated += 1
                    time.sleep(0.5)  # Slower rate limit for fallback
                except Exception as e2:
                    print(f"  Error updating row {row_num}: {e2}")
            print(f"✓ Updated {updated}/{len(results)} rows (fallback mode)")
    
    def run(self, gid: Optional[str] = None, limit: Optional[int] = None):
        """
        Run the Pano AI usage check for utilities
        
        Args:
            gid: Google Sheet tab ID (optional)
            limit: Maximum number of utilities to check (None for all)
        """
        print(f"Opening Google Sheet: {self.sheet_id}")
        self.open_sheet(gid)
        
        print(f"\nFinding or creating columns...")
        pano_col_index = self.find_or_create_column("Using Pano AI")
        source_col_index = self.find_or_create_column("Pano AI Source")
        
        # Find the starting row based on "Using Pano AI" column (primary)
        start_row = self.find_start_row(pano_col_index)
        
        print(f"✓ Starting to populate from row {start_row} (first empty row in 'Using Pano AI' column)")
        if limit:
            print(f"⚠️  LIMIT MODE: Only checking first {limit} utilities")
        
        print(f"\nReading utilities from column A...")
        utilities = self.get_utilities_from_column_a(start_row, limit=limit)
        
        if not utilities:
            print("No utilities found to check")
            return
        
        print(f"\nChecking Pano AI usage for {len(utilities)} utilities...")
        results = []
        
        for row_num, utility_name in utilities:
            try:
                is_using_pano_ai, source_urls = self.check_pano_ai_usage(utility_name)
                results.append((row_num, is_using_pano_ai, source_urls))
                time.sleep(1)  # Rate limiting between utilities
            except Exception as e:
                print(f"  Error checking {utility_name}: {e}")
                results.append((row_num, False, []))  # Default to False with no sources on error
        
        print(f"\nUpdating Google Sheet with results...")
        self.update_sheet(results, pano_col_index, source_col_index)
        
        print(f"\n✅ Completed! Checked {len(results)} utilities.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check utilities in Google Sheets for Pano AI camera usage"
    )
    parser.add_argument(
        "--sheet-id",
        default="1o9w1f7Ff6PVHEtNKTR8Na2l2AK2khanrDQEzFPyzW84",
        help="Google Sheet ID (default: from URL)"
    )
    parser.add_argument(
        "--gid",
        default="894070952",
        help="Google Sheet GID/tab ID (default: from URL)"
    )
    parser.add_argument(
        "--credentials",
        help="Path to OAuth2 client credentials JSON file (required)"
    )
    parser.add_argument(
        "--token",
        help="Path to OAuth2 token file (default: token.pickle)"
    )
    parser.add_argument(
        "--serpapi-key",
        help="SerpAPI key (optional, can use SERPAPI_KEY env var)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of utilities to check (useful for testing)"
    )
    
    args = parser.parse_args()
    
    try:
        checker = SheetsPanoAIChecker(
            sheet_id=args.sheet_id,
            serpapi_key=args.serpapi_key,
            credentials_path=args.credentials,
            token_path=args.token
        )
        checker.run(gid=args.gid, limit=args.limit)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

