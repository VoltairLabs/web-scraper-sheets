#!/bin/bash
# Script to run the next 100 rows that don't have values in Uses_Drones column

# Activate virtual environment
source venv/bin/activate

# Load base environment variables
source setup_env.sh

# Override to process next 100 new rows
export SKIP_EXISTING="True"
export MAX_ROWS="0"  # Process all rows (not limited to first N)
export MAX_NEW_ROWS="100"  # Stop after processing 100 new rows

echo ""
echo "Running next 100 rows (skipping existing values)..."
echo ""

# Run the script
python main.py

