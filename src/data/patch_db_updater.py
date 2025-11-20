import hashlib
import shutil
import requests
from pathlib import Path


class DBUpdater:
    GITHUB_OWNER = "Just-Yuura"
    GITHUB_REPO = "P5XCalculator"
    FILE_PATH = "/data/patch_db.json"
    BRANCH = "main"

    def __init__(self, local_file_path="patch_db.json"):
        self.local_file = Path(local_file_path)
        self.backup_file = self.local_file.parent / "patch_db.json.backup"


    def get_github_file_info(self):
        url = (
            f"https://api.github.com/repos/{self.GITHUB_OWNER}/"
            f"{self.GITHUB_REPO}/contents/{self.FILE_PATH}?ref={self.BRANCH}"
        )

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None


    def download_file(self, download_url):
        try:
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()

            if self.local_file.exists():
                shutil.copy2(self.local_file, self.backup_file)

            with open(self.local_file, "wb") as f:
                f.write(response.content)

            if self.backup_file.exists():
                self.backup_file.unlink()

            return True
        except requests.RequestException:
            if self.backup_file.exists():
                shutil.copy2(self.backup_file, self.local_file)
                self.backup_file.unlink()

            return False


    def check_and_update(self):
        file_info = self.get_github_file_info()

        if not file_info:
            return

        download_url = file_info.get("download_url")

        if not download_url:
            return

        if not self.local_file.exists():
            self.download_file(download_url)

            return

        remote_sha = file_info.get("sha")
        local_sha = self.calculate_git_sha(self.local_file)

        if remote_sha == local_sha:
            return

        self.download_file(download_url)


    @staticmethod
    def calculate_git_sha(file_path):
        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            git_blob = f"blob {len(data)}\0".encode() + data

            return hashlib.sha1(git_blob).hexdigest()
        except IOError:
            return None