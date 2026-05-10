import sys
import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; daily-info-digest/1.0)"}


def fetch_github_trending(language: str = "", since: str = "daily", max_repos: int = 5) -> list[dict]:
    url = f"https://github.com/trending/{language}" if language else "https://github.com/trending"
    resp = requests.get(url, params={"since": since}, headers=_HEADERS, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.select("article.Box-row")[:max_repos]:
        h2 = article.select_one("h2 a")
        if not h2:
            continue

        name = " ".join(h2.get_text().split())  # collapse whitespace
        repo_url = "https://github.com" + h2["href"]

        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        stars_el = article.select_one("a[href$='/stargazers']")
        stars = stars_el.get_text(strip=True) if stars_el else "?"

        repos.append({
            "title": name,
            "url": repo_url,
            "summary": description,
            "stars": stars,
        })

    if not repos and resp.status_code == 200:
        print(
            "[warn] github trending: page returned 200 but no repos parsed"
            " — HTML structure may have changed",
            file=sys.stderr,
        )

    return repos
