import requests
import os
import subprocess

def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        capture_output=True,
        text=True
    )
    files = result.stdout.strip().split("\n")
    return files

def read_file(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Could not read file: {e}"

def analyze_with_ai(code):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "OPENAI_API_KEY not found."

    prompt = f"""
You are a senior software engineer.
Review the following code and find:
1. Logical bugs
2. Edge cases
3. Incorrect assumptions

Code:
{code}
"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
    )

    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    files = get_changed_files()

    print("📂 Changed files detected:\n")

    for file in files:
        if file.strip() == "":
            continue
        print(f"📄 File: {file}")
        
        code = read_file(file)

        print("----- CODE START -----")
        print(code)
        print("----- CODE END -----")

        print("🤖 AI LOGICAL REVIEW:")
        print(analyze_with_ai(code))
        print("\n")
