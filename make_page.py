#!/usr/bin/env python3
"""
Helper script to create wiki entity/event/concept pages from source texts.
Usage: python3 make_page.py <type> <name> <category> <tags>

Searches raw text files for mentions and creates a skeleton page.
"""

import os, re, json, sys
from collections import defaultdict
from datetime import datetime

WIKI = os.path.expanduser("~/hermes/history/United Kingdom 1865-1919/wiki")
RAW = os.path.join(WIKI, "raw")
ENTITIES = os.path.join(WIKI, "entities")
EVENTS = os.path.join(WIKI, "events")
CONCEPTS = os.path.join(WIKI, "concepts")

# Map source slugs to human-readable titles
SOURCE_TITLES = {
    "mccarthy-history-vol4": "McCarthy, Justin — A History of Our Own Times, Vol. IV (1865–1880)",
    "mccarthy-history-vol5-1880-1897": "McCarthy, Justin — A History of Our Own Times, Vol. V (1880–1897)",
    "mccarthy-diamond-jubilee-vol1": "McCarthy, Justin — A History of Our Own Times, Diamond Jubilee Vol. I (1897–1899)",
    "mccarthy-diamond-jubilee-vol2": "McCarthy, Justin — A History of Our Own Times, Diamond Jubilee Vol. II (1899–1901)",
    "annual-register-1901": "The Annual Register 1901",
    "annual-register-1902": "The Annual Register 1902",
    "annual-register-1903": "The Annual Register 1903",
    "annual-register-1904": "The Annual Register 1904",
    "annual-register-1905": "The Annual Register 1905",
    "annual-register-1906": "The Annual Register 1906",
    "annual-register-1907": "The Annual Register 1907",
    "annual-register-1908": "The Annual Register 1908",
    "annual-register-1909": "The Annual Register 1909",
    "annual-register-1910": "The Annual Register 1910",
    "annual-register-1911": "The Annual Register 1911",
    "annual-register-1912": "The Annual Register 1912",
    "annual-register-1913": "The Annual Register 1913",
    "annual-register-1914": "The Annual Register 1914",
    "annual-register-1915": "The Annual Register 1915",
    "annual-register-1916": "The Annual Register 1916",
    "annual-register-1917": "The Annual Register 1917",
    "annual-register-1918": "The Annual Register 1918",
    "annual-register-1919": "The Annual Register 1919",
    "clayton-rise-of-democracy": "Clayton, Joseph — The Rise of the Democracy (1911)",
    "lombard-street": "Bagehot, Walter — Lombard Street (1873)",
    "langer-diplomacy-imperialism-vol1": "Langer, William L. — The Diplomacy of Imperialism, Vol. I (1890–1902)",
    "langer-diplomacy-imperialism-vol2": "Langer, William L. — The Diplomacy of Imperialism, Vol. II (1890–1902)",
    "politics-grand-strategy": "Williamson, Samuel R. — The Politics of Grand Strategy (1904–1914)",
    "churchill-world-crisis-vol1": "Churchill, Winston S. — The World Crisis, Vol. I (1911–1914)",
    "corbett-naval-ops-vol1": "Corbett, Sir Julian S. — Naval Operations, Vol. I (1914)",
    "corbett-naval-ops-vol2": "Corbett, Sir Julian S. — Naval Operations, Vol. II (1915)",
    "corbett-naval-ops-vol3": "Corbett, Sir Julian S. — Naval Operations, Vol. III (1915–1916)",
    "corbett-naval-ops-vol4": "Corbett, Sir Julian S. — Naval Operations, Vol. IV (1916–1917)",
    "corbett-naval-ops-vol5": "Corbett, Sir Julian S. — Naval Operations, Vol. V (1917–1918)",
    "hankey-man-of-secrets-vol1": "Roskill, Stephen — Hankey: Man of Secrets, Vol. I (1877–1918)",
    "mackinder-british-seas": "Mackinder, Halford J. — Britain and the British Seas (1907)",
    "mackinder-eight-lectures-india": "Mackinder, Halford J. — Eight Lectures on India (1910)",
}


def find_raw_files():
    """Find all raw.txt files in the raw directory."""
    for root, dirs, files in os.walk(RAW):
        for f in files:
            if f == "raw.txt":
                yield os.path.join(root, f)


def slugify(name):
    """Convert entity name to file slug."""
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s


def search_sources(search_terms, context_lines=2):
    """Search all raw source texts for given terms. Returns {source_slug: [(line_no, context_snippet), ...]}"""
    results = defaultdict(list)
    terms = search_terms if isinstance(search_terms, list) else [search_terms]
    
    for raw_path in find_raw_files():
        # Get source slug from path
        rel = os.path.relpath(raw_path, RAW)
        slug = rel.split(os.sep)[0]
        
        with open(raw_path, 'r', errors='replace') as f:
            for i, line in enumerate(f, 1):
                line_lower = line.lower()
                # Check if any search term appears (case insensitive)
                if any(t.lower() in line_lower for t in terms):
                    # Get context
                    results[slug].append((i, line.rstrip()[:200]))
    
    return dict(results)


def make_entity_page(name, lifespan, category, tags, description):
    """Create an entity page file."""
    slug = slugify(name)
    title = f"{name} ({lifespan})" if lifespan else name
    
    # Search for this entity
    search_terms = [name]
    if '(' in name:
        main_name = name.split('(')[0].strip()
        search_terms.append(main_name)
    
    # Also search by surname
    parts = name.split()
    if len(parts) > 1:
        surname = parts[-1].strip('()')
        search_terms.append(surname)
    
    # Find relevant sources
    hits = search_sources(list(set(search_terms)))
    
    # Build frontmatter
    sources_yaml = ""
    for slug_key in sorted(hits.keys()):
        title_key = SOURCE_TITLES.get(slug_key, slug_key)
        count = len(hits[slug_key])
        previews = [f"Line {ln}: {txt[:100]}" for ln, txt in hits[slug_key][:3]]
        sources_yaml += f'  - source: "{slug_key}"\n'
        role = f"{count} mentions"
    if previews:
        role += " - " + previews[0][:80]
    sources_yaml += f'    role: "{role}"\n'
    
    content = f"""---
title: "{title}"
type: "entity"
category: "{category}"
tags:
{chr(10).join(f'  - {t}' for t in tags)}
sources:
{sources_yaml}---
"""
    # More detailed content would go below, but this is a starter
    out_path = os.path.join(ENTITIES, f"{slug}.md")
    with open(out_path, 'w') as f:
        f.write(content)
    
    return out_path, dict(hits)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 make_page.py <type> <name> <category> [tags...]")
        print("Example: python3 make_page.py entity 'Disraeli, Benjamin' prime-minister conservative reform")
        sys.exit(1)
    
    ptype = sys.argv[1]
    name = sys.argv[2]
    category = sys.argv[3]
    tags = sys.argv[4:] if len(sys.argv) > 4 else []
    
    if ptype == "entity":
        path, hits = make_entity_page(name, None, category, tags, "")
        print(f"Created: {path}")
        for src, matches in sorted(hits.items()):
            print(f"  {src}: {len(matches)} matches")
