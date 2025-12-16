#!/bin/bash
# Script to run the next 200 rows that don't have values in Uses_Drones column

# Activate virtual environment
source venv/bin/activate

# Load base environment variables
source setup_env.sh

# Override to process next 200 new rows
export SKIP_EXISTING="True"
export MAX_ROWS="0"  # Process all rows (not limited to first N)
export MAX_NEW_ROWS="200"  # Stop after processing 200 new rows

echo ""
echo "Running next 200 rows (skipping existing values)..."
echo ""

# Run the script
python main.py

