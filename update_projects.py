import os
import requests
from datetime import datetime, timedelta, timezone

GITHUB_USERNAME = "HugoDemont62"
REPO_COUNT = 5
README_PATH = "README.md"
REQUEST_TIMEOUT = 10  # seconds

def get_recent_repos():
    """Fetch the most recently pushed repos (non-fork, non-archived), limited by REPO_COUNT."""
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

    response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
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

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        missing = []
        if start_idx == -1:
            missing.append(start_marker)
        if end_idx == -1:
            missing.append(end_marker)
        missing_str = ", ".join(repr(m) for m in missing)
        raise RuntimeError(
            f"Unable to update {README_PATH}: missing marker(s) {missing_str}. "
            "Please ensure the markers are present in the README."
        )

    start_idx += len(start_marker)

    if start_idx > end_idx:
        raise RuntimeError(
            f"Unable to update {README_PATH}: markers {start_marker!r} and "
            f"{end_marker!r} are in the wrong order."
        )

    utc_plus_1 = timezone(timedelta(hours=1))
    now = datetime.now(timezone.utc).astimezone(utc_plus_1)
    now_str = now.strftime("%d/%m/%Y à %H:%M UTC+1")
    updated_line = f"\n> 🕐 Dernière mise à jour : {now_str}\n"

    new_content = (
        content[:start_idx]
        + "\n"
        + table
        + "\n"
        + updated_line
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
