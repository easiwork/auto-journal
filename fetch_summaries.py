import os
import requests
import sys
import re
import datetime
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Process iMessage conversations and generate summaries.')
parser.add_argument('--use-chatgpt', action='store_true', help='Use ChatGPT instead of Ollama')
args = parser.parse_args()

# Config
FOLDER_PATH = "./Assets"
CONVERTED_MESSAGES_FILE = os.path.join(FOLDER_PATH, "converted_messages.txt")

# Set up API details based on which service is being used
if args.use_chatgpt:
    print("Using ChatGPT for summaries...")
    API_URL = "https://api.openai.com/v1/chat/completions"
    API_KEY = os.environ.get("OPENAI_API_KEY")
    if not API_KEY:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)
    MODEL = "gpt-3.5-turbo"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
else:
    print("Using Ollama (llama3.2) for summaries...")
    API_URL = "http://localhost:11434/api/chat"
    MODEL = "llama3.2"
    HEADERS = {"Content-Type": "application/json"}

# Prompts
system_prompt = {
    "role": "system",
    "content": '''
you're helping me summarize a chunk of an iMessage conversation

below is part of the transcript. each message includes:
	•	a timestamp
	•	the sender's name ("Me" means a message from me. others are labeled with their names)
	•	the message text
	•	sometimes: tapback reactions (e.g. "Loved by …", "Laughed by …")

it might be a group convo with 3 or more people

read it and give me a one to two sentence summary, in second-person, saying who you were talking to and what it was about (e.g. "you were talking to sarah about weekend plans and her new job")

don't introduce the summary. don't refer to anyone as "they said" or "you said"—just use natural language like you're casually recounting what the convo was about.

here's the conversation:
'''
}

# Check if server is live before sending request (only for Ollama)
if not args.use_chatgpt:
    try:
        health_check = requests.get("http://localhost:11434", timeout=5)
        if health_check.status_code != 200:
            print(f"Ollama server at http://localhost:11434 is not responding properly. Status code: {health_check.status_code}")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"Ollama server at http://localhost:11434 is not accessible.")
        print("Run 'ollama serve' in another tab before running this script.")
        sys.exit(1)

# Check if converted_messages.txt exists
if not os.path.exists(CONVERTED_MESSAGES_FILE):
    print(f"Error: {CONVERTED_MESSAGES_FILE} not found.")
    print("Make sure text_to_person_mapper.py has been run first.")
    sys.exit(1)

print(f"\nProcessing {CONVERTED_MESSAGES_FILE}...")

# Read the file contents
with open(CONVERTED_MESSAGES_FILE, "r", encoding="utf-8") as f:
    file_content = f.read()

# Split the content by conversation sections
# The pattern matches "=== Content from..." section headers
conversations = re.split(r'(===\s+Content\s+from\s+.*?===)', file_content)

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Get yesterday's date in MM_DD format for default output directory
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
default_date_dir = yesterday.strftime("%m_%d")

# Clear the combined summary file - put it in a date directory
combined_summary_path = os.path.join("output", default_date_dir, "daily_summary.txt")
os.makedirs(os.path.dirname(combined_summary_path), exist_ok=True)
with open(combined_summary_path, "w", encoding="utf-8") as f:
    f.write(f"Daily Summary - {os.path.basename(CONVERTED_MESSAGES_FILE)}\n\n")

# Function to process API response based on the model being used
def extract_content_from_response(response_json, is_chatgpt=False):
    if is_chatgpt:
        return response_json["choices"][0]["message"]["content"]
    else:
        return response_json["message"]["content"]

# Process each conversation
conversation_count = 0
for i in range(1, len(conversations), 2):
    if i + 1 < len(conversations):
        # Get the header and content for this conversation
        header = conversations[i]
        content = conversations[i + 1].strip()
        
        # Skip if content is too short
        if len(content) < 50:
            continue
            
        # Extract date directory from header if possible (pattern: "=== Content from MM_DD/filename.txt ===")
        date_dir = default_date_dir
        date_match = re.search(r'===\s+Content\s+from\s+(\d{2}_\d{2})/', header)
        if date_match:
            date_dir = date_match.group(1)
        
        # Create output directory for this date
        date_output_dir = os.path.join("output", date_dir)
        os.makedirs(date_output_dir, exist_ok=True)
            
        conversation_count += 1
        print(f"\nProcessing conversation {conversation_count}: {header} (Output dir: {date_dir})")
        
        try:
            # Prepare the request payload based on the API being used
            if args.use_chatgpt:
                payload = {
                    "model": MODEL,
                    "messages": [
                        system_prompt,
                        {"role": "user", "content": content}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            else:
                payload = {
                    "model": MODEL,
                    "messages": [
                        system_prompt,
                        {"role": "user", "content": content}
                    ],
                    "stream": False
                }
            
            # Send the request
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                timeout=30  # seconds
            )
            
            if response.status_code == 200:
                print(f"Request succeeded for conversation {conversation_count}")
                data = response.json()
                
                # Extract content based on the API being used
                summary_content = extract_content_from_response(data, args.use_chatgpt)
                
                # Generate conversation-specific summary file in date directory
                model_prefix = "gpt_" if args.use_chatgpt else "llama_"
                conv_filename = f"{model_prefix}conversation_{conversation_count}_summary.txt"
                conv_path = os.path.join(date_output_dir, conv_filename)
                
                # Write individual summary to file
                with open(conv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n\n")
                    f.write(summary_content)
                print(f"Wrote summary to {conv_path}")
                
                # Append to combined summary
                with open(combined_summary_path, "a", encoding="utf-8") as f:
                    f.write(f"{header}\n\n")
                    f.write(summary_content)
                    f.write("\n\n" + "-" * 40 + "\n\n")
                
            else:
                print(f"Request failed for conversation {conversation_count}: {response.status_code}")
                print(response.text)
        except requests.RequestException as e:
            print(f"Error sending request for conversation {conversation_count}: {e}")

if conversation_count == 0:
    print("No conversations found in the file.")
else:
    print(f"\nProcessed {conversation_count} conversations.")
    print(f"Combined summary written to {combined_summary_path}")

