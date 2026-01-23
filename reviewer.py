iimport requests
import os
import subprocess
import json


def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n")


def read_file(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return "Could not read file: " + str(e)


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


def detect_performance_issues(code):
    issues = []
    lines = code.split("\n")
    loop_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("for ") or stripped.startswith("while "):
            loop_count += 1

    if loop_count >= 2:
        issues.append("⚠️ Possible nested loops detected (O(n²) complexity).")

    if "range(len(") in code:
        issues.append("⚠️ Using range(len()). Consider direct iteration.")

    if not issues:
        issues.append("✅ No obvious performance issues detected.")

    return issues


if __name__ == "__main__":
    files = get_changed_files()
    print("📂 Changed files detected:\n")

    for file in files:
        if not file.strip():
            continue

        print(f"📄 File: {file}")
        code = read_file(file)

        print("----- CODE START -----")
        print(code)
        print("----- CODE END -----")

        print("🤖 AI LOGICAL REVIEW:")
        print(analyze_with_ai(code))
        print("\n")

        print("⚡ PERFORMANCE REVIEW:")
        for issue in detect_performance_issues(code):
            print(issue)

        print("\n")
