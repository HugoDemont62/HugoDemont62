import os
import requests
from datetime import datetime

GITHUB_USERNAME = "HugoDemont62"
REPO_COUNT = 5
README_PATH = "README.md"

def get_recent_repos():
    """Fetch the 5 most recently pushed repos (non-fork, non-archived)."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    params = {
        "sort": "pushed",
        "direction": "desc",
        "per_page": 50,
        "type": "owner",
    }

    headers = {}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    repos = response.json()

    # Filter: skip forks and archived repos, also skip the profile repo itself
    filtered = [
        r for r in repos
        if not r.get("fork")
        and not r.get("archived")
        and r["name"].lower() != GITHUB_USERNAME.lower()
    ]

    return filtered[:REPO_COUNT]


def build_table(repos):
    """Build a markdown table from a list of repos."""
    rows = []
    rows.append("| Projet | Description | Langage | ⭐ | Dernière MàJ |")
    rows.append("|--------|-------------|---------|-----|--------------|")

    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        desc = (repo["description"] or "—").replace("|", "\\|")
        lang = repo["language"] or "—"
        stars = repo["stargazers_count"]
        pushed = datetime.strptime(
            repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%d/%m/%Y")

        rows.append(
            f"| [{name}]({url}) | {desc} | `{lang}` | {stars} | {pushed} |"
        )

    return "\n".join(rows)


def update_readme(table):
    """Replace the content between PROJECTS-START and PROJECTS-END markers."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- PROJECTS-START -->"
    end_marker = "<!-- PROJECTS-END -->"

    start_idx = content.index(start_marker) + len(start_marker)
    end_idx = content.index(end_marker)

    new_content = (
        content[:start_idx]
        + "\n"
        + table
        + "\n"
        + content[end_idx:]
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ README mis à jour avec {REPO_COUNT} projets récents.")


def main():
    repos = get_recent_repos()
    table = build_table(repos)
    update_readme(table)


if __name__ == "__main__":
    main()
