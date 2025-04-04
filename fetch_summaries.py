import os
import requests
import sys

# Config
FOLDER_PATH = "./Assets"
SERVER_URL = "http://localhost:11434"

# Prompts
system_prompt = {
    "role": "system",
    "content": '''
You're helping me summarize a chunk of an iMessage conversation.

Below is a portion of the conversation, formatted like a human-readable transcript. Each message includes:
- A timestamp
- The sender's name (a message sent by me will be labeled "Me". Other people will be labeled accordingly.)
- The message text
- Occasionally: tapback reactions (e.g., “Loved by ...”, "Laughed by ...")

A conversation could be a group conversation between 3 or more distinct senders.

When a message's sender is labeled "Me", that is a message that I sent.

Read the conversation and return:
1. A single sentence, in **first-person**, mentioning who the conversation was with and what this part of the conversation was about.
2. A **bulleted list**, also in first-person, capturing the main things that were said, asked, or shared—one bullet per distinct topic or idea.

Avoid summarizing the emotional tone of the conversation or interpreting feelings. Just focus on the actual content, using natural, casual first-person language as if I were recalling what was discussed.

Do not say "here's the summary", just provide the result. Do not refer to other people in second-person.

Here is the conversation:
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

# Loop through .txt files in the folder
for filename in os.listdir(FOLDER_PATH):
    if filename.endswith(".txt"):
        file_path = os.path.join(FOLDER_PATH, filename)
        print(f"\nProcessing {file_path}...")

        # Read the file contents
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        try:
            response = requests.post(
                SERVER_URL + '/api/chat',
                json={
                    "model": "llama3.2",
                    "messages": [
                        system_prompt,
                        {
                            "role": "user",
                            "content": file_content,
                        }
                    ],
                    "stream": False
                },
                timeout=30  # seconds
            )
            if response.status_code == 200:
                print("Request succeeded")
                data = response.json()

                # Create output directory if it doesn't exist
                os.makedirs("output", exist_ok=True)
                
                # Generate output filename
                output_filename = os.path.join("output", f"{os.path.splitext(filename)[0]}_summary.txt")
                
                # Write summary to file
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(data["message"]["content"])
                print(f"Wrote summary to {output_filename}")
                # Also append to combined summary file
                with open("output/combined_summary.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n=== Summary for {filename} ===\n")
                    f.write(data["message"]["content"])
                print("Appended to combined summary file")
            else:
                print("Request failed:", response.status_code)
        except requests.RequestException as e:
            print(f"Error sending {filename}: {e}")
# Print combined summary file contents
try:
    with open("output/combined_summary.txt", "r", encoding="utf-8") as f:
        print("\nCombined summaries:")
        print("-" * 40)
        print(f.read())
        print("-" * 40)
except FileNotFoundError:
    print("\nNo combined summary file found.")

