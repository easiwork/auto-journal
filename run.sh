#!/bin/bash

# Install or check for uv first
./check_install_uv.sh

# Check if contacts.vcf exists
if [ ! -f "./Assets/contacts.vcf" ]; then
    echo "Error: contacts.vcf file not found in Assets directory."
    echo "Please export your contacts from your address book and save as Assets/contacts.vcf"
    exit 1
fi

# Source the virtual environment
if [ -d ".venv" ]; then
    echo "Activating .venv virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating venv virtual environment..."
    source venv/bin/activate
else
    echo "Warning: No virtual environment found. Using system Python."
fi

# Convert contacts.vcf to CSV if it exists
echo "Converting contacts to CSV format..."
python Assets/contacts_to_csv.py

# Get yesterday's date in YYYY-MM-DD format for the start date
yesterday=$(date -v-1d +"%Y-%m-%d")
# Get today's date in YYYY-MM-DD format for the end date
today=$(date +"%Y-%m-%d")
# Get yesterday's date in MM_DD format for the output directory
output_dir=$(date -v-1d +"%m_%d")

# Set the output directory path using a relative path
export_path="./Assets/$output_dir"

# Create the output directory if it doesn't exist
mkdir -p "$export_path"

# Check if the export directory is empty
if [ ! "$(ls -A "$export_path")" ]; then
    echo "iMessage exports not found. Generating them now..."
    imessage-exporter -f txt -o "$export_path" -s "$yesterday" -e "$today" -a macOS
    echo "iMessage export complete."
else
    echo "iMessage exports already exist in $export_path"
fi

# Map phone numbers to contact names
echo "Mapping phone numbers to contact names..."
python text_to_person_mapper.py

# Run the fetch_summaries script
echo "Fetching summaries..."
uv run fetch_summaries.py

# Deactivate the virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

