"""Firecrawl collector for university admission data.

Collects clean markdown from a university's admission pages
for use with setup_rag.py.

Set FIRECRAWL_API_KEY in keys.env.
"""

import argparse
import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv("keys.env")

DEFAULT_ADMISSION_PATHS = [
    "admission", "postuplenie", "rules", "прием", "документы",
    "сроки", "экзамены", "льготы", "общежитие", "faq", "вступительные"
]


def get_firecrawl_client() -> Firecrawl:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY not found. "
            "Add it to keys.env or environment variables."
        )
    return Firecrawl(api_key=api_key)


def discover_relevant_urls(client: Firecrawl, start_url: str, limit: int = 100) -> List[str]:
    """Use map to find relevant admission pages."""
    try:
        result = client.map(
            url=start_url,
            limit=limit,
            search="поступление правила сроки документы экзамены FAQ льготы общежитие"
        )
        urls = result.get("links", []) if isinstance(result, dict) else getattr(result, "links", [])
        relevant = []
        for url in urls:
            u = url.lower()
            if any(p in u for p in DEFAULT_ADMISSION_PATHS) or "pk." in u or "admission" in u:
                relevant.append(url)
        return relevant[:limit]
    except Exception as e:
        print(f"Map failed, falling back to start_url only: {e}")
        return [start_url]


def scrape_pages(client: Firecrawl, urls: List[str], formats: List[str] = None) -> List[Dict]:
    """Scrape list of URLs to markdown + metadata."""
    if formats is None:
        formats = ["markdown", "metadata"]
    results = []
    for url in urls:
        try:
            doc = client.scrape(url, formats=formats)
            if doc:
                results.append({
                    "url": url,
                    "markdown": getattr(doc, "markdown", "") or doc.get("markdown", ""),
                    "metadata": getattr(doc, "metadata", {}) or doc.get("metadata", {})
                })
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
    return results


def structure_to_entries(scraped: List[Dict], university_name: str) -> List[Dict]:
    """Convert scraped pages into entries suitable for RAG indexing."""
    entries = []
    for item in scraped:
        text = item["markdown"]
        if not text.strip():
            continue
        title = item["metadata"].get("title", item["url"])
        section = item["metadata"].get("ogTitle", title)
        entry = {
            "text": f"# {title}\n\n{text}",
            "source": item["url"],
            "section": section,
            "metadata": {
                "university": university_name,
                "url": item["url"]
            }
        }
        entries.append(entry)
    return entries


def save_entries(entries: List[Dict], output_dir: Path, prefix: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{prefix}_rules.json"
    md_path = output_dir / f"{prefix}_raw.md"

    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(e["text"] + "\n\n---\n\n")

    print(f"Saved {len(entries)} entries to {json_path} and {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Collect university admission data using Firecrawl.")
    parser.add_argument("--start-url", required=True, help="Starting admission page URL")
    parser.add_argument("--name", required=True, help="Short university identifier (e.g. mipt)")
    parser.add_argument("--output-dir", default="data", help="Output directory for collected data")
    parser.add_argument("--limit", type=int, default=50, help="Max pages to crawl")
    args = parser.parse_args()

    client = get_firecrawl_client()

    print(f"Discovering relevant pages from {args.start_url}...")
    urls = discover_relevant_urls(client, args.start_url, args.limit)
    print(f"Found {len(urls)} relevant URLs")

    print("Scraping pages...")
    scraped = scrape_pages(client, urls)
    print(f"Scraped {len(scraped)} pages")

    entries = structure_to_entries(scraped, args.name)

    out = Path(args.output_dir) / args.name
    save_entries(entries, out, args.name)

    print(f"\nDone. Use the generated JSON in setup_rag.py for this university.")
    print(f"Example: python setup_rag.py --bachelor {out / (args.name + '_rules.json')} ...")


if __name__ == "__main__":
    main()
