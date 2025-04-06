import os
import requests
import sys
import re

# Config
FOLDER_PATH = "./Assets"
SERVER_URL = "http://localhost:11434"
CONVERTED_MESSAGES_FILE = os.path.join(FOLDER_PATH, "converted_messages.txt")

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

read it and give me:
	1.	a one-sentence summary, in second-person, saying who you were talking to and what it was about (e.g. "you were talking to sarah about weekend plans and her new job")
	2.	a bulleted list, also in second-person, covering what was said or shared—one bullet per idea or topic. stick to just the actual content. don't summarize tone or emotions.

don't introduce the summary. don't refer to anyone as "they said" or "you said"—just use natural language like you're casually recounting what the convo was about.

here's the conversation:
'''
}

# Check if server is live before sending request
try:
    health_check = requests.get(SERVER_URL, timeout=5)
    if health_check.status_code != 200:
        print(f"Server at {SERVER_URL} is not responding properly. Status code: {health_check.status_code}")
        sys.exit(1)
except requests.RequestException as e:
    print(f"Server at {SERVER_URL} is not accessible.")
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

# Clear the combined summary file
combined_summary_path = os.path.join("output", "daily_summary.txt")
with open(combined_summary_path, "w", encoding="utf-8") as f:
    f.write(f"Daily Summary - {os.path.basename(CONVERTED_MESSAGES_FILE)}\n\n")

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
            
        conversation_count += 1
        print(f"\nProcessing conversation {conversation_count}: {header}")
        
        try:
            response = requests.post(
                SERVER_URL + '/api/chat',
                json={
                    "model": "llama3.2",
                    "messages": [
                        system_prompt,
                        {
                            "role": "user",
                            "content": content,
                        }
                    ],
                    "stream": False
                },
                timeout=30  # seconds
            )
            if response.status_code == 200:
                print(f"Request succeeded for conversation {conversation_count}")
                data = response.json()
                
                # Generate conversation-specific summary file
                conv_filename = f"conversation_{conversation_count}_summary.txt"
                conv_path = os.path.join("output", conv_filename)
                
                # Write individual summary to file
                with open(conv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n\n")
                    f.write(data["message"]["content"])
                print(f"Wrote summary to {conv_path}")
                
                # Append to combined summary
                with open(combined_summary_path, "a", encoding="utf-8") as f:
                    f.write(f"{header}\n\n")
                    f.write(data["message"]["content"])
                    f.write("\n\n" + "-" * 40 + "\n\n")
                
            else:
                print(f"Request failed for conversation {conversation_count}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error sending request for conversation {conversation_count}: {e}")

if conversation_count == 0:
    print("No conversations found in the file.")
else:
    print(f"\nProcessed {conversation_count} conversations.")
    print(f"Combined summary written to {combined_summary_path}")

