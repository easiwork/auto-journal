#!/bin/zsh

# Default to using Ollama
USE_CHATGPT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --use-chatgpt)
            USE_CHATGPT=true
            shift
            ;;
        --api-key=*)
            export OPENAI_API_KEY="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# If using ChatGPT, ensure we have an API key
if [[ "$USE_CHATGPT" = true ]]; then
    if [[ -z "${OPENAI_API_KEY}" ]]; then
        echo "Error: OpenAI API key not provided. Please set OPENAI_API_KEY environment variable or use --api-key option."
        exit 1
    fi
fi

# Check for required installations
if ! command -v imessage-exporter &> /dev/null; then
    echo "Error: imessage-exporter not found. Please install it first."
    exit 1
fi

# Check for contacts.vcf in Assets directory
if [[ ! -f "Assets/contacts.vcf" ]]; then
    echo "Error: contacts.vcf not found in Assets directory."
    exit 1
fi

# Activate virtual environment if it exists
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# Convert contacts to CSV
python3 contacts_to_csv.py

# Get yesterday's date in YYYY-MM-DD format
yesterday=$(date -v-1d +"%Y-%m-%d")
today=$(date +"%Y-%m-%d")

# Generate iMessage exports for the past day
imessage-exporter --export-path Assets --start-date "$yesterday" --end-date "$today"

# Fetch summaries using either ChatGPT or Ollama
if [[ "$USE_CHATGPT" = true ]]; then
    echo "Using ChatGPT for generating summaries..."
    python3 fetch_summaries.py --use-chatgpt
else
    echo "Using Ollama for generating summaries..."
    python3 fetch_summaries.py
fi
