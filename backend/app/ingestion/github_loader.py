
import re
import subprocess

from pathlib import Path
from urllib.parse import urlsplit


class GitHubLoader:

    def __init__(self):
        self.github_domain = "github.com"

    def validate_github_url(self, repository_url: str):

        """
        Validate that the URL points to a public GitHub repository.
        """

        parsed = urlsplit(repository_url.strip())

        if parsed.scheme != "https":
            raise ValueError("Only HTTPS GitHub URLs are allowed.")

        if parsed.hostname != self.github_domain:
            raise ValueError("Only github.com repositories are supported.")

        if parsed.username or parsed.password:
            raise ValueError("Credentials in repository URLs are not allowed.")

        if parsed.query or parsed.fragment:
            raise ValueError("Query parameters and fragments are not allowed.")

        parts = [
            part for part in parsed.path.strip("/").split("/")
            if part
        ]

        if len(parts) != 2:
            raise ValueError(
                "Invalid GitHub URL. Expected: "
                "https://github.com/owner/repository"
            )

        owner, repository = parts

        repository = repository.removesuffix(".git")

        valid_name = re.compile(r"^[A-Za-z0-9_.-]+$")

        if not valid_name.fullmatch(owner):
            raise ValueError("Invalid repository owner.")

        if not valid_name.fullmatch(repository):
            raise ValueError("Invalid repository name.")

        clean_url = (
            f"https://github.com/{owner}/{repository}.git"
        )

        return {
            "owner": owner,
            "repository": repository,
            "url": clean_url
        }

    def clone_repository(
        self,
        repository_url: str,
        destination: Path,
        branch: str | None = None
    ):

        """
        Clone a public GitHub repository using shallow cloning.
        """

        repository_info = self.validate_github_url(repository_url)

        destination = Path(destination).resolve()

        if destination.exists():
            raise FileExistsError(
                "Repository destination already exists."
            )

        command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch"
        ]

        if branch:
            if (
                not re.fullmatch(r"[A-Za-z0-9._/-]{1,128}", branch)
                or branch.startswith("-")
                or ".." in branch.split("/")
            ):
                raise ValueError("Invalid branch name.")

            command.extend(["--branch", branch])

        command.extend([
            repository_info["url"],
            str(destination)
        ])

        try:

            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
                env={
                    **__import__("os").environ,
                    "GIT_TERMINAL_PROMPT": "0"
                }
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Repository cloning timed out."
            )

        except subprocess.CalledProcessError as error:
            message = error.stderr[-2000:] if error.stderr else ""

            raise RuntimeError(
                f"Git clone failed: {message}"
            )

        # Retrieve latest commit hash
        commit_result = subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "rev-parse",
                "HEAD"
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15
        )

        return {
            **repository_info,
            "local_path": str(destination),
            "commit_hash": commit_result.stdout.strip()
        }
