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

# Activate virtual environment if it exists
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# Convert contacts to CSV only if contacts_reformatted.csv doesn't exist
if [[ ! -f "Assets/contacts_reformatted.csv" ]]; then
    # Check for contacts.vcf in Assets directory
    if [[ ! -f "Assets/contacts.vcf" ]]; then
        echo "Error: contacts.vcf not found in Assets directory."
        exit 1
    fi
    echo "Converting contacts to CSV..."
    python3 contacts_to_csv.py
else
    echo "Using existing contacts_reformatted.csv..."
fi

# Get yesterday's date in YYYY-MM-DD format
yesterday=$(date -v-1d +"%Y-%m-%d")
yesterday_dir=$(date -v-1d +"%m_%d")
today=$(date +"%Y-%m-%d")

# Debug prints
echo "[run.sh] Yesterday: $yesterday"
echo "[run.sh] Today: $today"

# Generate iMessage exports for the past day
imessage-exporter -f txt -o "Assets/$yesterday_dir" -s "$yesterday" -e "$today" -a macOS

# Process the exported messages
echo "Processing exported messages..."
python3 text_to_person_mapper.py

# Fetch summaries using either ChatGPT or Ollama
if [[ "$USE_CHATGPT" = true ]]; then
    echo "Using ChatGPT for generating summaries..."
    python3 fetch_summaries.py --use-chatgpt
else
    echo "Using Ollama for generating summaries..."
    python3 fetch_summaries.py
fi
