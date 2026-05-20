import os
import requests
from datetime import datetime, timedelta, timezone

GITHUB_USERNAME = "HugoDemont62"
REPO_COUNT = 5
README_PATH = "README.md"
REQUEST_TIMEOUT = 10

def get_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def fetch_paginated(url, params=None):
    """Fetch all pages from a GitHub API endpoint."""
    results = []
    params = params or {}
    params["per_page"] = 100
    page = 1
    while True:
        params["page"] = page
        r = requests.get(url, params=params, headers=get_headers(), timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        results.extend(data)
        # Si moins de 100 résultats, c'est la dernière page
        if len(data) < 100:
            break
        page += 1
    return results

def get_orgs():
    """Récupère les orgs de l'utilisateur authentifié (nécessite GH_TOKEN)."""
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("⚠️  Pas de GH_TOKEN : les repos d'organisations ne seront pas inclus.")
        return []
    try:
        return fetch_paginated("https://api.github.com/user/orgs")
    except requests.HTTPError as e:
        print(f"⚠️  Impossible de récupérer les orgs : {e}")
        return []

def get_all_repos():
    """Récupère les repos perso + ceux de toutes les orgs, filtrés et triés."""
    # Repos personnels
    personal = fetch_paginated(
        f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
        params={"sort": "pushed", "direction": "desc", "type": "owner"},
    )

    # Repos des orgs
    org_repos = []
    for org in get_orgs():
        org_name = org["login"]
        repos = fetch_paginated(f"https://api.github.com/orgs/{org_name}/repos")
        org_repos.extend(repos)

    all_repos = personal + org_repos

    # Dédoublonnage par id, filtre forks/archivés/profil
    seen = set()
    filtered = []
    for r in all_repos:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        if r.get("fork") or r.get("archived"):
            continue
        if r["name"].lower() == GITHUB_USERNAME.lower():
            continue
        filtered.append(r)

    # Tri par pushed_at décroissant
    filtered.sort(key=lambda r: r["pushed_at"], reverse=True)

    return filtered[:REPO_COUNT]

def build_table(repos):
    rows = [
        "| Projet | Description | Langage | ⭐ | Dernière MàJ |",
        "|--------|-------------|---------|-----|--------------|",
    ]
    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        desc = (repo["description"] or "—").replace("|", "\\|")
        lang = repo["language"] or "—"
        stars = repo["stargazers_count"]
        pushed = datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
        # Préfixe org si ce n'est pas un repo perso
        owner = repo["owner"]["login"]
        display_name = f"{owner}/{name}" if owner.lower() != GITHUB_USERNAME.lower() else name
        rows.append(f"| [{display_name}]({url}) | {desc} | `{lang}` | {stars} | {pushed} |")
    return "\n".join(rows)

def update_readme(table):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- PROJECTS-START -->"
    end_marker = "<!-- PROJECTS-END -->"
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        missing = [m for m, i in [(start_marker, start_idx), (end_marker, end_idx)] if i == -1]
        raise RuntimeError(f"Marqueur(s) manquant(s) dans {README_PATH} : {missing}")

    start_idx += len(start_marker)
    if start_idx > end_idx:
        raise RuntimeError("Les marqueurs sont dans le mauvais ordre.")

    utc_plus_1 = timezone(timedelta(hours=1))
    now = datetime.now(timezone.utc).astimezone(utc_plus_1)
    now_str = now.strftime("%d/%m/%Y à %H:%M UTC+1")
    updated_line = f"\n> 🕐 Dernière mise à jour : {now_str}\n"

    new_content = content[:start_idx] + "\n" + table + "\n" + updated_line + content[end_idx:]
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ README mis à jour avec {REPO_COUNT} projets récents (perso + orgs).")

def main():
    repos = get_all_repos()
    table = build_table(repos)
    update_readme(table)

if __name__ == "__main__":
    main()
