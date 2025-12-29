"""Google Sheets integration module."""
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class GoogleSheetsHandler:
    """Handler for Google Sheets operations."""
    
    def __init__(self, credentials_file: str, sheet_id: str, sheet_name: str = 'Sheet1'):
        """
        Initialize the Google Sheets handler.
        
        Args:
            credentials_file: Path to credentials JSON file
            sheet_id: Google Sheet ID from the URL
            sheet_name: Name of the worksheet (default: Sheet1)
        """
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            # Try service account first (recommended for automation)
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
        except Exception as e:
            # Fall back to OAuth if service account fails
            logger.warning(f"Service account auth failed: {e}. Trying OAuth...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                self.client = gspread.authorize(creds)
            except Exception as e2:
                logger.error(f"OAuth authentication failed: {e2}")
                raise
        
        # Open the spreadsheet
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            self.sheet = spreadsheet.worksheet(self.sheet_name)
        except Exception as e:
            logger.error(f"Error opening sheet: {e}")
            raise
    
    def append_data(self, data: List[Dict], headers: Optional[List[str]] = None):
        """
        Append data to the sheet.
        
        Args:
            data: List of dictionaries containing data to append
            headers: Optional list of header names (uses dict keys if not provided)
        """
        if not data:
            logger.warning("No data to append")
            return
        
        # Get headers from first dict if not provided
        if headers is None:
            headers = list(data[0].keys())
        
        # Check if headers exist, if not add them
        existing_headers = self.sheet.row_values(1)
        if not existing_headers or existing_headers != headers:
            self.sheet.insert_row(headers, 1)
        
        # Append rows
        rows = [[row.get(header, '') for header in headers] for row in data]
        self.sheet.append_rows(rows)
        logger.info(f"Appended {len(rows)} rows to sheet")
    
    def update_data(self, data: List[Dict], start_row: int = 2, headers: Optional[List[str]] = None):
        """
        Update existing data in the sheet.
        
        Args:
            data: List of dictionaries containing data to update
            start_row: Row number to start updating from (default: 2, assuming row 1 is headers)
            headers: Optional list of header names (uses dict keys if not provided)
        """
        if not data:
            logger.warning("No data to update")
            return
        
        if headers is None:
            headers = list(data[0].keys())
        
        # Update rows
        for idx, row_data in enumerate(data):
            row_num = start_row + idx
            values = [row_data.get(header, '') for header in headers]
            self.sheet.update(f'A{row_num}', [values])
        
        logger.info(f"Updated {len(data)} rows in sheet")
    
    def clear_and_update(self, data: List[Dict], headers: Optional[List[str]] = None):
        """
        Clear existing data and update with new data.
        
        Args:
            data: List of dictionaries containing data
            headers: Optional list of header names (uses dict keys if not provided)
        """
        if headers is None and data:
            headers = list(data[0].keys())
        
        # Clear the sheet
        self.sheet.clear()
        
        # Add headers and data
        if headers:
            self.sheet.insert_row(headers, 1)
        
        if data:
            rows = [[row.get(header, '') for header in headers] for row in data]
            self.sheet.append_rows(rows)
        
        logger.info(f"Cleared and updated sheet with {len(data)} rows")

