#!/usr/bin/env python3
"""
Generate entity, event, and concept pages for the UK 1865-1919 wiki.
Searches raw text files and builds narrative pages with source references.
"""

import os, re, sys

WIKI = os.path.expanduser("~/hermes/history/United Kingdom 1865-1919/wiki")
RAW = os.path.join(WIKI, "raw")
ENTITIES = os.path.join(WIKI, "entities")
EVENTS = os.path.join(WIKI, "events")
CONCEPTS = os.path.join(WIKI, "concepts")
SOURCES = os.path.join(WIKI, "sources")

os.makedirs(ENTITIES, exist_ok=True)
os.makedirs(EVENTS, exist_ok=True)
os.makedirs(CONCEPTS, exist_ok=True)

def slugify(name):
    s = name.lower().replace("'", "")
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def get_raw_files():
    """Return list of raw.txt paths."""
    files = []
    for root, dirs, fnames in os.walk(RAW):
        for f in fnames:
            if f == "raw.txt":
                files.append(os.path.join(root, f))
    return sorted(files)

def grep_file(path, pattern, context=0):
    """Simple grep returning (line_no, line) matches."""
    results = []
    pat = pattern.lower()
    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if pat in line.lower():
                results.append((i, line.rstrip()))
    return results

def source_slug_from_path(raw_path):
    rel = os.path.relpath(raw_path, RAW)
    return rel.split(os.sep)[0]

# ─── ENTITY PAGES ──────────────────────────────────────────

ENTITIES_DEF = {
    "George V": {
        "type": "entity",
        "category": "monarch",
        "tags": ["crown", "empire", "great-war"],
        "search_terms": ["King George V", "George V", "the King"],
        "exclude_terms": ["George of Greece", "George Washington"],
    },
    "Disraeli, Benjamin": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["conservative", "imperialism", "reform"],
        "search_terms": ["Disraeli", "Lord Beaconsfield", "Beaconsfield"],
    },
    "Gladstone, William Ewart": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["liberal", "home-rule", "reform"],
        "search_terms": ["Gladstone", "Mr. Gladstone", "W. E. Gladstone"],
    },
    "Salisbury, 3rd Marquess of": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["conservative", "imperialism", "foreign-policy"],
        "search_terms": ["Salisbury", "Lord Salisbury", "Marquess of Salisbury"],
    },
    "Balfour, Arthur James": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["conservative", "unionist", "defence"],
        "search_terms": ["Balfour", "A. J. Balfour", "Arthur Balfour"],
    },
    "Campbell-Bannerman, Henry": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["liberal", "south-africa", "reform"],
        "search_terms": ["Campbell-Bannerman", "Sir Henry Campbell-Bannerman"],
    },
    "Asquith, Herbert Henry": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["liberal", "great-war", "home-rule"],
        "search_terms": ["Asquith", "H. H. Asquith", "Prime Minister"],
    },
    "Lloyd George, David": {
        "type": "entity",
        "category": "prime-minister",
        "tags": ["liberal", "great-war", "welfare", "budget"],
        "search_terms": ["Lloyd George", "David Lloyd George"],
    },
}

def search_entity(name, terms, exclude_terms=None):
    """Search raw files for entity mentions. Returns {source_slug: [(line_no, line)]}"""
    results = {}
    for raw_path in get_raw_files():
        slug = source_slug_from_path(raw_path)
        found = []
        for term in terms:
            for ln, line in grep_file(raw_path, term):
                if exclude_terms:
                    skip = False
                    for ex in exclude_terms:
                        if ex.lower() in line.lower():
                            skip = True
                            break
                    if skip:
                        continue
                found.append((ln, line))
        if found:
            results[slug] = found[:50]  # cap at 50 per source
    return results

def read_section(raw_path, line_no, width=10):
    """Read a window of lines around a given line."""
    lines = []
    with open(raw_path, 'r', errors='replace') as f:
        all_lines = f.readlines()
    start = max(0, line_no - width - 1)
    end = min(len(all_lines), line_no + width)
    for i in range(start, end):
        lines.append((i+1, all_lines[i].rstrip()))
    return lines

def make_entity_page(name, defn):
    """Create a narrative entity page."""
    slug = slugify(name)
    terms = defn["search_terms"]
    exclude = defn.get("exclude_terms", [])
    
    # Search
    hits = search_entity(name, terms, exclude)
    
    sources_yaml = []
    for src in sorted(hits.keys()):
        count = len(hits[src])
        sources_yaml.append(f"  - source: \"{src}\"\n    role: \"{count} mentions\"")
    
    tags_yaml = "\n".join(f"  - {t}" for t in defn["tags"])
    
    content = f"""---
title: "{name}"
type: entity
category: {defn['category']}
tags:
{tags_yaml}
sources:
{chr(10).join(sources_yaml)}
---

"""
    
    out_path = os.path.join(ENTITIES, f"{slug}.md")
    with open(out_path, 'w') as f:
        f.write(content)
    
    return out_path, hits

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode == "all":
        for name, defn in ENTITIES_DEF.items():
            path, hits = make_entity_page(name, defn)
            print(f"✓ {name} -> {path}")
            for src, lines in sorted(hits.items()):
                print(f"    {src}: {len(lines)} hits")
    elif mode == "show":
        # Show top passages for a given entity
        name = sys.argv[2]
        defn = ENTITIES_DEF[name]
        hits = search_entity(name, defn["search_terms"], defn.get("exclude_terms", []))
        for src in sorted(hits.keys()):
            print(f"\n=== {src} ===")
            for ln, line in hits[src][:10]:
                print(f"  L{ln}: {line[:150]}")
