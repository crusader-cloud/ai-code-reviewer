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

if __name__ == "__main__":
    files = get_changed_files()

    print("📂 Changed files detected:\n")

    for file in files:
        if file.strip() == "":
            continue
        print(f"📄 File: {file}")
        content = read_file(file)
        print("----- CODE START -----")
        print(content)
        print("----- CODE END -----\n")
