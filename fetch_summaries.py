import os
import requests

# Config
FOLDER_PATH = "./Assets"
SERVER_URL = "http://localhost:11434/api/chat"

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

# Loop through .txt files in the folder
for filename in os.listdir(FOLDER_PATH):
    if filename.endswith(".txt"):
        file_path = os.path.join(FOLDER_PATH, filename)
        print(f"\nSending {file_path}...")

        # Read the file contents
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        try:
            # Send POST request
            response = requests.post(
                SERVER_URL,
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
                print(f"##### Summary start for {filename} #####\n\n")
                print(data["message"]["content"])
                print("\n##### Summary end #####")
            else:
                print("Request failed:", response.status_code)
        except requests.RequestException as e:
            print(f"Error sending {filename}: {e}")
