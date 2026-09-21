#!/usr/bin/env python3
"""
Sonic Physics Guide (SPG) Scraper & Markdown Converter
Scrapes all chapters and subtopics of the Sonic Physics Guide from Sonic Retro (info.sonicretro.org)
and formats them into clean, self-contained Markdown with local images and cross-links.
"""

import os
import sys
import re
import json
import time
import urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

API_BASE = "https://info.sonicretro.org/api.php"
USER_AGENT = "SonicPhysicsDocBot/1.0 (+https://sonicretro.org)"
HEADERS = {"User-Agent": USER_AGENT}

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
IMAGES_DIR = ROOT_DIR / "images"

# Canonical chapter order and mapping
PAGES = [
    {
        "wiki_title": "Sonic Physics Guide",
        "file": "docs/00-overview.md",
        "title": "Sonic Physics Guide: Overview",
        "section": "Core",
    },
    {
        "wiki_title": "SPG:Basics",
        "file": "docs/01-basics.md",
        "title": "Basics: Objects, Maps, Subpixels, Angles, and Framerates",
        "section": "Core",
    },
    {
        "wiki_title": "SPG:Calculations",
        "file": "docs/02-calculations.md",
        "title": "Calculations: Angle Ranges & Trigonometric Functions",
        "section": "Core",
    },
    {
        "wiki_title": "SPG:Characters",
        "file": "docs/03-characters.md",
        "title": "Characters: Sonic, Tails, and Knuckles Physics Differences",
        "section": "Core",
    },
    {
        "wiki_title": "SPG:Solid Tiles",
        "file": "docs/04-terrain-collision.md",
        "title": "Terrain Collision: Solid Tiles, Block Data, and Sensors",
        "section": "Collision",
    },
    {
        "wiki_title": "SPG:Solid Terrain",
        "file": "docs/05-terrain-interaction.md",
        "title": "Terrain Interaction: Collision Layers and Loop Physics",
        "section": "Collision",
    },
    {
        "wiki_title": "SPG:Slope Collision",
        "file": "docs/06-slope-collision.md",
        "title": "Slope Collision: Sensors, Grounded, 360°, and Airborne",
        "section": "Collision",
    },
    {
        "wiki_title": "SPG:Hitboxes",
        "file": "docs/07-hitboxes.md",
        "title": "Hitboxes: Player Hitbox and Trigger Areas",
        "section": "Collision",
    },
    {
        "wiki_title": "SPG:Solid Objects",
        "file": "docs/08-solid-objects.md",
        "title": "Solid Objects: Slopes, Platforms, Blocks, and Monitors",
        "section": "Collision",
    },
    {
        "wiki_title": "SPG:Slope Physics",
        "file": "docs/09-slope-physics.md",
        "title": "Slope Physics: Moving, Slipping, 360° Momentum, and Landing",
        "section": "Physics",
    },
    {
        "wiki_title": "SPG:Forces",
        "file": "docs/10-forces.md",
        "title": "Forces: Physics Values, Running, Jumping, Rolling, and Impact",
        "section": "Physics",
    },
    {
        "wiki_title": "SPG:Air State",
        "file": "docs/11-forces-subtopics/air-state.md",
        "title": "Forces Subtopic: Air State & Midair Momentum",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Jumping",
        "file": "docs/11-forces-subtopics/jumping.md",
        "title": "Forces Subtopic: Jumping & Variable Jump Height",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Rolling",
        "file": "docs/11-forces-subtopics/rolling.md",
        "title": "Forces Subtopic: Rolling Physics & Rolling Jump",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Getting Hit",
        "file": "docs/11-forces-subtopics/getting-hit.md",
        "title": "Forces Subtopic: Getting Hit & Invulnerability Frames",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Rebound",
        "file": "docs/11-forces-subtopics/rebound.md",
        "title": "Forces Subtopic: Rebounding & Boss Impact",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Underwater",
        "file": "docs/11-forces-subtopics/underwater.md",
        "title": "Forces Subtopic: Underwater Physics & Buoyancy",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Super Speeds",
        "file": "docs/11-forces-subtopics/super-speeds.md",
        "title": "Forces Subtopic: Speed Shoes, Super & Hyper Sonic Speeds",
        "section": "Forces Deep Dives",
    },
    {
        "wiki_title": "SPG:Main Game Loop",
        "file": "docs/12-main-game-loop.md",
        "title": "Main Game Loop: Execution Order per Frame",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Game Objects",
        "file": "docs/13-game-objects.md",
        "title": "Game Objects: Springs, Spikes, Rings, Monitors, and Bumpers",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Game Enemies",
        "file": "docs/14-game-enemies.md",
        "title": "Game Enemies: Badniks and Bosses Mechanics",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Ring Loss",
        "file": "docs/15-ring-loss.md",
        "title": "Ring Loss: Scatter Trajectories, Speeds, and Timers",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Special Abilities",
        "file": "docs/16-special-abilities.md",
        "title": "Special Abilities: Spindash, Peel Out, Drop Dash, Flight, Glide",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Elemental Shields",
        "file": "docs/17-elemental-shields.md",
        "title": "Elemental Shields: Flame, Bubble, and Lightning Shield Actions",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Player 2",
        "file": "docs/18-player-2.md",
        "title": "Player 2: CPU AI, Follower Physics, and Respawning",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Special Stages",
        "file": "docs/19-special-stages.md",
        "title": "Special Stages: Sonic 1 Rotating Maze Physics",
        "section": "Gameplay",
    },
    {
        "wiki_title": "SPG:Camera",
        "file": "docs/20-camera.md",
        "title": "Camera: Scrolling Boundaries, Lag, and Pan Delays",
        "section": "Presentation",
    },
    {
        "wiki_title": "SPG:Animations",
        "file": "docs/21-animations.md",
        "title": "Animations: Scripts, Variable Speed Timings, and Rules",
        "section": "Presentation",
    },
    {
        "wiki_title": "SPG:Overlay Scripts",
        "file": "docs/22-overlay-scripts.md",
        "title": "Overlay Scripts: Diagnostic HUDs for Sonic 1 & Sonic 2",
        "section": "Special",
    },
]

WIKI_TITLE_TO_FILE = {p["wiki_title"]: p["file"] for p in PAGES}
for p in PAGES:
    WIKI_TITLE_TO_FILE[p["wiki_title"].replace(" ", "_")] = p["file"]

def slugify(text: str) -> str:
    """Converts a heading string to a GitHub markdown compatible anchor slug."""
    text = text.lower().strip()
    text = re.sub(r'[\.\,\:\;\(\)\'\"\?\!\/]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def get_relative_link(source_file: str, target_file: str) -> str:
    """Calculates relative file link between two paths."""
    src_parent = Path(source_file).parent
    tgt = Path(target_file)
    rel = os.path.relpath(tgt, src_parent)
    return rel.replace("\\", "/")

def get_images_rel_path(source_file: str) -> str:
    """Calculates relative path to images/ folder from source markdown file."""
    src_parent = Path(source_file).parent
    rel = os.path.relpath(IMAGES_DIR, src_parent)
    return rel.replace("\\", "/")

class MarkdownFormatter:
    def __init__(self, source_file: str):
        self.source_file = source_file
        self.img_rel_dir = get_images_rel_path(source_file)

    def format_node(self, node) -> str:
        # Ignore HTML comments (such as NewPP limit report)
        if isinstance(node, Comment):
            return ""

        if isinstance(node, NavigableString):
            return str(node)

        if not isinstance(node, Tag):
            return ""

        # Ignore elements to strip
        if node.get("id") == "toc":
            return ""
        classes = node.get("class", [])
        if "breakout" in classes or "mw-editsection" in classes or "printfooter" in classes:
            return ""

        tag = node.name

        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            for es in node.find_all(class_="mw-editsection"):
                es.decompose()
            text = self.format_children(node).strip()
            return f"\n\n{'#' * level} {text}\n\n"

        if tag == "p":
            text = self.format_children(node).strip()
            if not text:
                return ""
            # Format Note and Important as GitHub alert blockquotes
            if re.match(r'^(?:\*\*)?(?:Note|NOTE):(?:\*\*)?\s*', text, re.IGNORECASE):
                cleaned = re.sub(r'^(?:\*\*)?(?:Note|NOTE):(?:\*\*)?\s*', '', text, flags=re.IGNORECASE)
                lines = [f"> {line}" for line in cleaned.split("\n")]
                return f"\n\n> [!NOTE]\n" + "\n".join(lines) + "\n\n"
            if re.match(r'^(?:\*\*)?(?:Important|IMPORTANT):(?:\*\*)?\s*', text, re.IGNORECASE):
                cleaned = re.sub(r'^(?:\*\*)?(?:Important|IMPORTANT):(?:\*\*)?\s*', '', text, flags=re.IGNORECASE)
                lines = [f"> {line}" for line in cleaned.split("\n")]
                return f"\n\n> [!IMPORTANT]\n" + "\n".join(lines) + "\n\n"
            return f"\n\n{text}\n\n"

        if tag == "br":
            return "<br>"

        if tag == "hr":
            return "\n\n---\n\n"

        if tag in ["b", "strong"]:
            text = self.format_children(node)
            if not text.strip():
                return text
            return f"**{text.strip()}**"

        if tag in ["i", "em"]:
            text = self.format_children(node)
            if not text.strip():
                return text
            return f"*{text.strip()}*"

        if tag in ["s", "del", "strike"]:
            text = self.format_children(node)
            return f"~~{text.strip()}~~"

        if tag == "code":
            return f"`{node.get_text()}`"

        if tag == "pre":
            code = node.get_text()
            # Clean wikitext bold markers ''' inside pre blocks
            code = code.replace("'''", "")
            return f"\n\n```c\n{code.strip()}\n```\n\n"

        if tag == "blockquote":
            text = self.format_children(node).strip()
            lines = [f"> {line}" for line in text.split("\n")]
            return "\n\n" + "\n".join(lines) + "\n\n"

        if tag in ["ul", "ol"]:
            return self.format_list(node)

        if tag == "table":
            return self.format_table(node)

        if tag == "a":
            return self.format_link(node)

        if tag == "img":
            return self.format_image(node)

        if tag == "div":
            if "thumb" in classes:
                return self.format_thumbnail(node)
            return self.format_children(node)

        if tag in ["span", "small", "big", "center", "font", "section"]:
            return self.format_children(node)

        if tag == "dl":
            return self.format_definition_list(node)

        return self.format_children(node)

    def format_children(self, node) -> str:
        parts = []
        for child in node.children:
            parts.append(self.format_node(child))
        return "".join(parts)

    def format_link(self, node: Tag) -> str:
        href = node.get("href", "")
        classes = node.get("class", [])

        # If it wraps an image and points to wiki File/Special page, just render the image
        img = node.find("img")
        if img and ("image" in classes or "/File:" in href or "/Special:FilePath" in href):
            return self.format_image(img)

        text = self.format_children(node).strip()
        if not text and img:
            return self.format_image(img)
        if not text:
            return ""

        if href.startswith("http://") or href.startswith("https://"):
            return f"[{text}]({href})"

        # Handle wiki internal links
        if href.startswith("/"):
            clean_href = href.lstrip("/")
            if clean_href.startswith("index.php?title="):
                clean_href = clean_href.replace("index.php?title=", "")
                clean_href = clean_href.split("&")[0]

            parts = clean_href.split("#", 1)
            page_title = urllib.parse.unquote(parts[0])
            anchor = parts[1] if len(parts) > 1 else ""

            matched_file = None
            for wt, file_path in WIKI_TITLE_TO_FILE.items():
                if wt.lower() == page_title.lower() or wt.replace(" ", "_").lower() == page_title.lower():
                    matched_file = file_path
                    break

            if matched_file:
                rel_path = get_relative_link(self.source_file, matched_file)
                if anchor:
                    anchor_slug = slugify(urllib.parse.unquote(anchor))
                    return f"[{text}]({rel_path}#{anchor_slug})"
                return f"[{text}]({rel_path})"
            elif anchor and not page_title:
                anchor_slug = slugify(urllib.parse.unquote(anchor))
                return f"[{text}](#{anchor_slug})"
            else:
                full_url = f"https://info.sonicretro.org/{clean_href}"
                return f"[{text}]({full_url})"

        return text

    def format_image(self, node: Tag) -> str:
        src = node.get("src", "")
        alt = node.get("alt", "")
        filename = os.path.basename(urllib.parse.unquote(src.split("?")[0]))
        if not alt or alt == filename:
            alt = Path(filename).stem.replace("_", " ").replace("SPG", "SPG ")
        return f"![{alt}]({self.img_rel_dir}/{filename})"

    def format_thumbnail(self, node: Tag) -> str:
        img_node = node.find("img")
        caption_node = node.find(class_="thumbcaption")
        caption = ""
        if caption_node:
            for es in caption_node.find_all(class_="magnify"):
                es.decompose()
            caption = self.format_children(caption_node).strip()

        if img_node:
            src = img_node.get("src", "")
            filename = os.path.basename(urllib.parse.unquote(src.split("?")[0]))
            alt = caption or Path(filename).stem.replace("_", " ")
            res = f"\n\n![{alt}]({self.img_rel_dir}/{filename})"
            if caption:
                res += f"\n\n*{caption}*\n"
            return res
        return ""

    def format_list(self, node: Tag, depth: int = 0) -> str:
        items = []
        is_ordered = node.name == "ol"
        idx = 1
        indent = "  " * depth

        for child in node.children:
            if not isinstance(child, Tag) or child.name != "li":
                continue

            sub_lists = []
            for sub in list(child.find_all(["ul", "ol"], recursive=False)):
                sub_lists.append(self.format_list(sub, depth + 1))
                sub.decompose()

            li_text = self.format_children(child).strip()
            prefix = f"{indent}{idx}. " if is_ordered else f"{indent}- "
            items.append(f"{prefix}{li_text}")
            for sl in sub_lists:
                items.append(sl)
            idx += 1

        return "\n" + "\n".join(items) + "\n"

    def format_definition_list(self, node: Tag) -> str:
        lines = []
        for child in node.children:
            if not isinstance(child, Tag):
                continue
            text = self.format_children(child).strip()
            if not text:
                continue
            if child.name == "dt":
                lines.append(f"\n**{text}**")
            elif child.name == "dd":
                lines.append(f": {text}")
        return "\n" + "\n".join(lines) + "\n"

    def format_table(self, table: Tag) -> str:
        classes = table.get("class", [])
        if "breakout" in classes:
            return ""

        # If table contains inner tables, unpack it cleanly
        if table.find("table"):
            blocks = []
            for tr in table.find_all("tr", recursive=False) or table.find_all("tr"):
                for cell in tr.find_all(["td", "th"], recursive=False):
                    if cell.find("table"):
                        for item in cell.children:
                            if isinstance(item, Tag) and item.name == "table":
                                blocks.append(self.format_table(item))
                            else:
                                formatted = self.format_node(item).strip()
                                if formatted:
                                    blocks.append(formatted)
                    else:
                        cell_content = self.format_children(cell).strip()
                        if cell_content:
                            blocks.append(cell_content)
            return "\n\n" + "\n\n".join(b for b in blocks if b) + "\n\n"

        rows = []
        for tr in table.find_all("tr", recursive=False) or table.find_all("tr"):
            row = []
            for cell in tr.find_all(["th", "td"], recursive=False):
                cell_text = self.format_children(cell).strip()
                cell_text = cell_text.replace("\n", " ").replace("|", "\\|")
                cell_text = re.sub(r"\s+", " ", cell_text)
                row.append(cell_text)
            if row:
                rows.append((tr, row))

        if not rows:
            return ""

        col_count = max(len(r[1]) for r in rows)
        if col_count == 0:
            return ""

        normalized_rows = []
        for tr, row in rows:
            padded = row + [""] * (col_count - len(row))
            normalized_rows.append(padded)

        out = []
        header = normalized_rows[0]
        data_rows = normalized_rows[1:]

        out.append("| " + " | ".join(header) + " |")
        out.append("| " + " | ".join(["---"] * col_count) + " |")
        for d in data_rows:
            out.append("| " + " | ".join(d) + " |")

        return "\n\n" + "\n".join(out) + "\n\n"


def clean_markdown(md: str) -> str:
    """Cleans up redundant empty lines and formatting artifacts."""
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = re.sub(r'[ \t]+$', '', md, flags=re.MULTILINE)
    return md.strip() + "\n"

def build_navigation(page_idx: int) -> str:
    """Builds top/bottom navigation bar for a chapter."""
    curr = PAGES[page_idx]
    prev_link = ""
    next_link = ""

    if page_idx > 0:
        prev_page = PAGES[page_idx - 1]
        rel_prev = get_relative_link(curr["file"], prev_page["file"])
        prev_link = f"[← {prev_page['title']}]({rel_prev})"

    if page_idx < len(PAGES) - 1:
        next_page = PAGES[page_idx + 1]
        rel_next = get_relative_link(curr["file"], next_page["file"])
        next_link = f"[{next_page['title']} →]({rel_next})"

    rel_root = get_relative_link(curr["file"], "README.md")

    parts = []
    if prev_link:
        parts.append(prev_link)
    parts.append(f"[Index]({rel_root})")
    if next_link:
        parts.append(next_link)

    return " | ".join(parts)


CACHE_DIR = ROOT_DIR / ".cache"
PAGE_CACHE_DIR = CACHE_DIR / "pages"

def get_with_retry(session, url, retries=5, backoff=1.5):
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp
            print(f"    HTTP {resp.status_code}, retrying ({attempt+1}/{retries})...")
        except Exception as e:
            print(f"    Request error: {e}, retrying ({attempt+1}/{retries})...")
        time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts.")

def fetch_all(force_refresh=False):
    print(f"Ensuring output directories exist...")
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "11-forces-subtopics").mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    all_images_needed = set()
    pages_content = {}

    print(f"\n--- 1. Fetching/Loading {len(PAGES)} Wiki Pages ---")
    for i, page_info in enumerate(PAGES):
        title = page_info["wiki_title"]
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
        cache_file = PAGE_CACHE_DIR / f"{safe_name}.json"

        if not force_refresh and cache_file.exists():
            print(f"[{i+1}/{len(PAGES)}] Loading from cache '{title}'...")
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            print(f"[{i+1}/{len(PAGES)}] Fetching '{title}' from API...")
            url = f"{API_BASE}?action=parse&page={urllib.parse.quote(title)}&prop=text|images&format=json"
            resp = get_with_retry(session, url)
            data = resp.json()
            if "error" in data:
                print(f"ERROR fetching {title}: {data['error']}")
                continue
            cache_file.write_text(json.dumps(data), encoding="utf-8")
            time.sleep(0.5)

        parse = data.get("parse", {})
        html_raw = parse.get("text", {}).get("*", "")
        imgs = parse.get("images", [])
        all_images_needed.update(imgs)
        pages_content[title] = (html_raw, imgs)

    print(f"\n--- 2. Resolving and Downloading {len(all_images_needed)} Images/Assets ---")
    image_list = list(all_images_needed)
    image_urls = {}
    batch_size = 50
    for i in range(0, len(image_list), batch_size):
        batch = image_list[i:i + batch_size]
        titles_param = "|".join([f"File:{fn}" for fn in batch])
        url = f"{API_BASE}?action=query&titles={urllib.parse.quote(titles_param)}&prop=imageinfo&iiprop=url&format=json"
        resp = session.get(url, timeout=30)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for pid, pdata in pages.items():
            fn = pdata.get("title", "").replace("File:", "")
            info = pdata.get("imageinfo", [{}])[0]
            if "url" in info:
                image_urls[fn] = info["url"]

    # Also extract any img src directly from the parsed HTML
    for title, (html_raw, _) in pages_content.items():
        soup = BeautifulSoup(html_raw, "html.parser")
        for b in soup.find_all("table", class_="breakout"):
            b.decompose()
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue
            filename = os.path.basename(urllib.parse.unquote(src.split("?")[0]))
            if filename not in image_urls:
                if src.startswith("//"):
                    image_urls[filename] = f"https:{src}"
                elif src.startswith("/"):
                    image_urls[filename] = f"https://info.sonicretro.org{src}"
                else:
                    image_urls[filename] = src

    downloaded = 0
    for fn, img_url in image_urls.items():
        dest = IMAGES_DIR / fn
        if dest.exists() and dest.stat().st_size > 0:
            continue
        try:
            r = session.get(img_url, timeout=30)
            if r.status_code == 200:
                dest.write_bytes(r.content)
                downloaded += 1
                if downloaded % 10 == 0:
                    print(f"  Downloaded {downloaded}/{len(image_urls)} assets...")
            time.sleep(0.05)
        except Exception as e:
            print(f"  Failed to download {fn} from {img_url}: {e}")

    print(f"Finished asset downloads. Total in images/: {len(list(IMAGES_DIR.iterdir()))}")

    print(f"\n--- 3. Converting Pages to Markdown ---")
    for idx, page_info in enumerate(PAGES):
        title = page_info["wiki_title"]
        file_path = ROOT_DIR / page_info["file"]
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if title not in pages_content:
            continue

        raw_html, _ = pages_content[title]
        soup = BeautifulSoup(raw_html, "html.parser")
        parser_output = soup.find("div", class_="mw-parser-output") or soup

        formatter = MarkdownFormatter(source_file=page_info["file"])
        body_md = formatter.format_node(parser_output)

        nav_bar = build_navigation(idx)
        canonical_url = f"https://info.sonicretro.org/{urllib.parse.quote(title.replace(' ', '_'))}"

        header_block = f"# {page_info['title']}\n\n"
        header_block += f"> **Source:** [{title}]({canonical_url})\n\n"
        header_block += f"{nav_bar}\n\n---\n\n"

        footer_block = f"\n\n---\n\n{nav_bar}\n"

        full_md = header_block + body_md + footer_block
        full_md = clean_markdown(full_md)

        file_path.write_text(full_md, encoding="utf-8")
        print(f"Wrote {page_info['file']} ({len(full_md)} chars)")

    print(f"\n--- 4. Generating Master README.md ---")
    generate_readme()
    print("Done! All documentation generated successfully.")

def generate_readme():
    readme_path = ROOT_DIR / "README.md"

    md = """# Sonic Physics Guide (SPG) Documentation

This repository contains a complete, offline-ready Markdown documentation suite for the **Sonic Physics Guide** from [Sonic Retro](https://info.sonicretro.org/Sonic_Physics_Guide).

The Sonic Physics Guide is the canonical reference detailing the exact mathematical models, object logic, terrain collision, slopes, angle systems, subpixel math, and frame-by-frame simulation used across classic Sega Genesis Sonic games (*Sonic the Hedgehog 1, Sonic the Hedgehog 2, Sonic CD, and Sonic the Hedgehog 3 & Knuckles*).

---

## Guide Conventions

| Concept | Specification | Description |
| --- | --- | --- |
| **Coordinate System** | Origin (0,0) Top-Left | X increases rightward, Y increases downward. |
| **Units** | Pixels & Subpixels | 1 Pixel = 256 Subpixels (range 0–255). |
| **Angle System** | Hex Angles (0–255) / Degrees | 0 = Right, 64 = Down, 128 = Left, 192 = Up (clockwise in Genesis hex, counter-clockwise in math notation). |
| **Target Framerate** | 60 FPS (NTSC) | Physics speeds and accelerations are applied per frame at 60 Hz. |
| **Collision Basis** | Whole Pixels | Subpixels are discarded during collision sensor tests. |

---

## Table of Contents

### 1. Core Mechanics
- **[00. Guide Overview](docs/00-overview.md)** - Introduction, purpose, and engine architecture.
- **[01. Basics](docs/01-basics.md)** - Hexadecimal, data types, **Objects** (variables, collision radius, hitboxes), level map hierarchy (Cells, Blocks, Chunks), subpixel math, angles, and framerates.
- **[02. Calculations](docs/02-calculations.md)** - Angle range classifications, sine/cosine conversion, fixed-point subpixel arithmetic.
- **[03. Characters](docs/03-characters.md)** - Physics attribute comparison between Sonic, Tails, and Knuckles.

### 2. Collision System
- **[04. Terrain Collision](docs/04-terrain-collision.md)** - Solid tile format, 16x16 block collision arrays, angle arrays, sensor probes.
- **[05. Terrain Interaction](docs/05-terrain-interaction.md)** - Collision layer switching, 360° vertical loop traversal mechanics.
- **[06. Slope Collision](docs/06-slope-collision.md)** - Sensor positioning (A, B, C, D, E, F), grounded slope snapping, wall pushers, airborne landing.
- **[07. Hitboxes](docs/07-hitboxes.md)** - Player interaction hitboxes vs. terrain radius boxes, item triggers, hurtboxes.
- **[08. Solid Objects](docs/08-solid-objects.md)** - Moving platforms, sloped objects, jump-through platforms, pushable blocks, item monitors.

### 3. Physics & Forces
- **[09. Slope Physics](docs/09-slope-physics.md)** - Slope factor acceleration, sliding thresholds, fall-off speeds, wall/ceiling adhesion.
- **[10. Forces & Movement](docs/10-forces.md)** - Master physics table: acceleration, deceleration, top speed, jumping, rolling, damage rebound, and water entry.
- **Forces Deep Dives:**
  - **[Air State](docs/11-forces-subtopics/air-state.md)** - Midair speed transitions, air acceleration, drag.
  - **[Jumping](docs/11-forces-subtopics/jumping.md)** - Jump impulse values, variable height cutoff logic.
  - **[Rolling](docs/11-forces-subtopics/rolling.md)** - Rolling friction, slope assist, rolling jump behavior.
  - **[Getting Hit](docs/11-forces-subtopics/getting-hit.md)** - Knockback trajectory, ring scatter triggers, invulnerability timers.
  - **[Rebound](docs/11-forces-subtopics/rebound.md)** - Badnik bounce-back and boss impact recoil.
  - **[Underwater](docs/11-forces-subtopics/underwater.md)** - Water physics dampening, buoyancy, gravity reduction.
  - **[Super Speeds](docs/11-forces-subtopics/super-speeds.md)** - Speed Shoes multiplier and Super/Hyper Sonic constants.

### 4. Gameplay Logic
- **[12. Main Game Loop](docs/12-main-game-loop.md)** - Frame execution order: Player control -> Object routine -> Collision -> Camera -> V-INT.
- **[13. Game Objects](docs/13-game-objects.md)** - Springs (vertical, horizontal, diagonal), Spikes, Rings, Item Monitors, Bumpers, Starposts.
- **[14. Game Enemies](docs/14-game-enemies.md)** - Badnik archetypes (Motobug, Chopper, Buzz Bomber, Crabmeat) and Boss logic.
- **[15. Ring Loss](docs/15-ring-loss.md)** - Ring scatter angle distribution, bouncing physics, collection lockout delay.
- **[16. Special Abilities](docs/16-special-abilities.md)** - Spindash, Super Peel Out, Drop Dash, Insta-Shield, Tails Flight/Swim, Knuckles Glide & Climb.
- **[17. Elemental Shields](docs/17-elemental-shields.md)** - Flame Shield (Fire Dash), Bubble Shield (Bounce Attack), Lightning Shield (Double Jump).
- **[18. Player 2 Logic](docs/18-player-2.md)** - Tails CPU companion AI, follow pathing, respawning flight.
- **[19. Special Stages](docs/19-special-stages.md)** - Sonic 1 360° rotating maze physics, bumper grid, goal triggers.

### 5. Presentation & Diagnostics
- **[20. Camera](docs/20-camera.md)** - Scrolling boundaries, look up/down delays, speed lag margins.
- **[21. Animations](docs/21-animations.md)** - Sprite animation scripts, frame duration formulas based on player speed.
- **[22. Overlay Scripts](docs/22-overlay-scripts.md)** - Gens/Lua diagnostic overlays for real-time sensor and speed monitoring.

---

## Quick Reference: Physics Constants (Sonic 1 / 2 / 3&K)

| Constant | Normal Value (Hex / Dec) | Underwater Value | Description |
| --- | --- | --- | --- |
| `acc` | `0x000C` (12 spx / 0.046875 px/frame) | `0x0006` (6 spx) | Acceleration per frame while holding direction |
| `dec` | `0x0080` (128 spx / 0.5 px/frame) | `0x0040` (64 spx) | Deceleration per frame when braking against motion |
| `frc` | `0x000C` (12 spx / 0.046875 px/frame) | `0x0006` (6 spx) | Friction per frame when coasting without input |
| `top` | `0x0600` (1536 spx / 6.0 px/frame) | `0x0300` (768 spx) | Normal maximum running speed on flat ground |
| `jmp` | `0x0680` (6.5 px/frame) / Knux `0x0600` | `0x0380` (3.5 px/frame) | Initial upward velocity applied on jump press |
| `grv` | `0x0038` (56 spx / 0.21875 px/frame) | `0x0010` (16 spx) | Downward acceleration applied each frame while airborne |
| `slp` | `0x0020` (32 spx / 0.125 px/frame) | `0x0020` (32 spx) | Slope factor added to Ground Speed when running on slopes |

---

## Updating the Documentation

To re-fetch and re-generate this documentation suite:

```bash
python3 scripts/scraper.py
```
"""
    readme_path.write_text(md.strip() + "\n", encoding="utf-8")
    print(f"Generated {readme_path}")

if __name__ == "__main__":
    fetch_all()
