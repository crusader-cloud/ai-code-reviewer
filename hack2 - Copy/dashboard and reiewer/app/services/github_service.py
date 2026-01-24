from github import Github, GithubIntegration
from typing import Optional, List, Dict, Any
import re


class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self, access_token: str):
        self.github = Github(access_token)
        self.user = self.github.get_user()
    
    def get_pull_request(self, repo_full_name: str, pr_number: int):
        """Get a pull request"""
        repo = self.github.get_repo(repo_full_name)
        return repo.get_pull(pr_number)
    
    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Any]:
        """Get files changed in a PR"""
        pr = self.get_pull_request(repo_full_name, pr_number)
        return list(pr.get_files())
    
    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> Dict[str, str]:
        """Get diff for each file in PR"""
        files = self.get_pr_files(repo_full_name, pr_number)
        diffs = {}
        
        for file in files:
            if file.patch:  # patch contains the diff
                diffs[file.filename] = file.patch
        
        return diffs
    
    def post_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int
    ) -> Optional[int]:
        """Post a review comment on a specific line"""
        try:
            pr = self.get_pull_request(repo_full_name, pr_number)
            comment = pr.create_review_comment(
                body=body,
                commit=pr.get_commits()[pr.commits - 1],  # Latest commit
                path=path,
                line=line
            )
            return comment.id
        except Exception as e:
            print(f"Error posting comment: {e}")
            return None
    
    def post_review_summary(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT"  # COMMENT, APPROVE, REQUEST_CHANGES
    ):
        """Post a review summary"""
        try:
            pr = self.get_pull_request(repo_full_name, pr_number)
            pr.create_review(body=body, event=event)
        except Exception as e:
            print(f"Error posting review: {e}")
    
    def get_file_content(
        self,
        repo_full_name: str,
        file_path: str,
        ref: str = "main"
    ) -> Optional[str]:
        """Get content of a file from repository"""
        try:
            repo = self.github.get_repo(repo_full_name)
            content = repo.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None
    
    def detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
        }
        
        for ext, lang in extension_map.items():
            if filename.endswith(ext):
                return lang
        
        return 'unknown'
    
    def parse_diff_line_numbers(self, diff: str) -> List[int]:
        """Extract line numbers from diff that were added/modified"""
        lines = []
        current_line = 0
        
        for line in diff.split('\n'):
            # Parse hunk header
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                # This is an added line
                lines.append(current_line)
                current_line += 1
            elif not line.startswith('-'):
                # Context line
                current_line += 1
        
        return lines
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature"""
        import hmac
        import hashlib
        
        expected_signature = 'sha256=' + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)


def get_github_service(access_token: str) -> GitHubService:
    """Get GitHub service instance"""
    return GitHubService(access_token)
