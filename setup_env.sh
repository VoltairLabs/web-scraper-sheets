#!/bin/bash
# Setup script for environment variables
# Run this before executing main.py: source setup_env.sh

export GOOGLE_CREDS_PATH="/Users/avigotskind/Downloads/GOOG.json"
export SPREADSHEET_ID="1E5-i7-MacB5MfYfs_do_fGD7-NFYGcU_tft-Ab-pPRg"
export SHEET_NAME="Main"
export SERPAPI_API_KEY="8821c01916831cf0a1a3c075f3043bf085496c07332e778934e67c622be8c98a"
export SKIP_EXISTING="True"
export MAX_ROWS="30"

echo "Environment variables set:"
echo "  GOOGLE_CREDS_PATH=$GOOGLE_CREDS_PATH"
echo "  SPREADSHEET_ID=$SPREADSHEET_ID"
echo "  SHEET_NAME=$SHEET_NAME"
echo "  SERPAPI_API_KEY=*** (hidden)"
if [ -n "$MAX_ROWS" ]; then
    echo "  MAX_ROWS=$MAX_ROWS (test mode - processing only first $MAX_ROWS rows)"
fi
echo ""
echo "✅ All configuration set! You can now run: python main.py"

