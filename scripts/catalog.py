#!/usr/bin/env python3
"""
Asset catalog tooling for images/ (stack-neutral, Python standard library only).

  python3 scripts/catalog.py sync       Refresh DERIVED fields in catalog/asset-manifest.json
  python3 scripts/catalog.py validate   Check the manifest against the schema and the filesystem
  python3 scripts/catalog.py report     Regenerate catalog/REVIEW.md from the manifest
  python3 scripts/catalog.py facts F..  Print derived technical facts for files (debugging)

Derived fields (owned by `sync`, verified by `validate`; never hand-edit):
  sha256, media.*, related_docs, provenance.source_pages,
  relationships.exact_duplicate_of, relationships.exact_duplicates

Everything else in the manifest is authored and is never touched by `sync`.
The tool never writes to images/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = "images"
CATALOG_DIR = ROOT / "catalog"
MANIFEST = CATALOG_DIR / "asset-manifest.json"
SCHEMA = CATALOG_DIR / "asset-manifest.schema.json"
REVIEW = CATALOG_DIR / "REVIEW.md"

IMG_EXTS = (".png", ".gif", ".svg", ".jpg", ".jpeg", ".webp", ".lua")
MIME = {"png": "image/png", "gif": "image/gif", "jpeg": "image/jpeg", "svg": "image/svg+xml", "lua": "text/x-lua"}
EXT_FORMATS = {".png": "png", ".gif": "gif", ".jpg": "jpeg", ".jpeg": "jpeg", ".svg": "svg", ".lua": "lua"}

# Stack-neutrality guard: the schema must not name implementation stacks.
FORBIDDEN_SCHEMA_TERMS = [
    "gpui", "rust", "canvas", "bevy", "godot", "unity", "unreal", "gamemaker", "clickteam",
    "react", "vue", "svelte", "electron", "webgl", "opengl", "vulkan", "wgpu", "sdl",
    "pygame", "phaser", "html", "css", "javascript", "typescript", "wasm", "cargo",
]

ENTRY_ORDER = [
    "id", "path", "sha256", "media", "kind", "tags", "summary", "depicts", "demonstrates",
    "sequence", "atlas", "runtime_role", "runtime_role_rationale", "implementation_notes",
    "related_docs", "provenance", "relationships", "verification", "confidence",
]
PROVENANCE_ORDER = [
    "cited_source_url", "cited_source_evidence", "source_pages", "acquisition", "creator",
    "creator_evidence", "license", "license_evidence", "rights_status", "rights_notes",
]


# ----------------------------------------------------------------------------------------
# Media parsing (headers only, plus a small PNG pixel decoder for alpha measurement)
# ----------------------------------------------------------------------------------------

PNG_SIG = b"\x89PNG\r\n\x1a\n"
PNG_COLOR = {0: "grayscale", 2: "rgb", 3: "indexed", 4: "grayscale-alpha", 6: "rgba"}
PNG_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _png_unfilter(raw: bytes, height: int, stride: int, bpp: int):
    rows, prev = [], bytearray(stride)
    pos = 0
    for _ in range(height):
        ft = raw[pos]
        cur = bytearray(raw[pos + 1: pos + 1 + stride])
        pos += 1 + stride
        if ft == 1:
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif ft == 2:
            for i in range(stride):
                cur[i] = (cur[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                left = cur[i - bpp] if i >= bpp else 0
                cur[i] = (cur[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 255
        elif ft != 0:
            raise ValueError(f"bad PNG filter {ft}")
        rows.append(cur)
        prev = cur
    return rows


def parse_png(data: bytes) -> dict:
    pos, chunks = 8, []
    while pos < len(data):
        ln, ctype = struct.unpack(">I4s", data[pos: pos + 8])
        chunks.append((ctype, data[pos + 8: pos + 8 + ln]))
        pos += 12 + ln
    ihdr = next(c for t, c in chunks if t == b"IHDR")
    w, h, bd, ct, _comp, _flt, interlace = struct.unpack(">IIBBBBB", ihdr)
    trns = next((c for t, c in chunks if t == b"tRNS"), None)
    animated_png = any(t == b"acTL" for t, _ in chunks)
    if ct in (4, 6):
        mode = "alpha-channel"
    elif ct == 3 and trns is not None:
        mode = "palette-transparency"
    elif trns is not None:
        mode = "color-key"
    else:
        mode = "none"
    out = {
        "format": "png", "width": w, "height": h, "color_model": PNG_COLOR[ct], "bit_depth": bd,
        "alpha_mode": mode, "has_transparent_pixels": None, "has_partial_alpha": None,
        "animated": animated_png, "frame_count": 1, "frame_timing": None,
    }
    if animated_png:
        out["frame_count"] = struct.unpack(">I", next(c for t, c in chunks if t == b"acTL")[:4])[0]
    if mode == "none":
        out["has_transparent_pixels"] = False
        out["has_partial_alpha"] = False
        return out
    if interlace != 0 or (mode == "color-key"):
        return out  # not measured
    raw = zlib.decompress(b"".join(c for t, c in chunks if t == b"IDAT"))
    ch = PNG_CHANNELS[ct]
    stride = (w * ch * bd + 7) // 8
    rows = _png_unfilter(raw, h, stride, max(1, ch * bd // 8))
    transparent = partial = False
    if ct == 6 and bd == 8:
        vals = set()
        for r in rows:
            vals.update(r[3::4])
    elif ct == 6 and bd == 16:
        vals = set()
        for r in rows:
            vals.update(r[6::8])
    elif ct == 4 and bd == 8:
        vals = set()
        for r in rows:
            vals.update(r[1::2])
    elif ct == 3:
        table = list(trns) + [255] * (256 - len(trns))
        idx = set()
        for r in rows:
            if bd == 8:
                idx.update(r)
            else:
                mask = (1 << bd) - 1
                for byte in r:
                    for shift in range(8 - bd, -1, -bd):
                        idx.add((byte >> shift) & mask)
        vals = {table[i] for i in idx if i < 256}
    else:
        return out
    transparent = any(v != 255 for v in vals)
    partial = any(0 < v < 255 for v in vals)
    out["has_transparent_pixels"] = transparent
    out["has_partial_alpha"] = partial
    return out


def _skip_subblocks(data: bytes, pos: int) -> int:
    while True:
        n = data[pos]
        pos += 1
        if n == 0:
            return pos
        pos += n


def parse_gif(data: bytes) -> dict:
    w, h, flags, _bg, _aspect = struct.unpack("<HHBBB", data[6:13])
    pos = 13
    if flags & 0x80:
        pos += 3 * (2 << (flags & 7))
    delays, gce, any_transparent, loop = [], None, False, None
    while pos < len(data):
        b = data[pos]
        pos += 1
        if b == 0x3B:
            break
        if b == 0x21:
            label = data[pos]
            pos += 1
            if label == 0xF9:
                fl = data[pos + 1]
                delay = struct.unpack("<H", data[pos + 2: pos + 4])[0]
                gce = (delay * 10, bool(fl & 1))
                pos = _skip_subblocks(data, pos)
            elif label == 0xFF:
                n = data[pos]
                app = data[pos + 1: pos + 1 + n]
                nxt = pos + 1 + n
                if app.startswith((b"NETSCAPE2.0", b"ANIMEXTS1.0")) and data[nxt] >= 3 and data[nxt + 1] == 1:
                    loop = struct.unpack("<H", data[nxt + 2: nxt + 4])[0]
                pos = _skip_subblocks(data, pos)
            else:
                pos = _skip_subblocks(data, pos)
        elif b == 0x2C:
            ifl = data[pos + 8]
            pos += 9
            if ifl & 0x80:
                pos += 3 * (2 << (ifl & 7))
            pos += 1
            pos = _skip_subblocks(data, pos)
            d, t = gce if gce else (0, False)
            delays.append(d)
            any_transparent = any_transparent or t
            gce = None
        else:
            raise ValueError("bad GIF block")
    n = len(delays)
    if loop is None:
        loop_kind, loop_count = "unspecified", None
    elif loop == 0:
        loop_kind, loop_count = "infinite", None
    else:
        loop_kind, loop_count = "finite", loop
    timing = None
    if n > 1:
        uniform = len(set(delays)) == 1
        timing = {
            "unit": "ms", "total_duration_ms": sum(delays),
            "uniform_delay_ms": delays[0] if uniform else None,
            "delays_ms": None if uniform else delays,
            "loop": loop_kind, "loop_count": loop_count,
        }
    return {
        "format": "gif", "width": w, "height": h, "color_model": "indexed", "bit_depth": 8,
        "alpha_mode": "palette-transparency" if any_transparent else "none",
        # A declared transparent index (often used for delta frames) does not prove the composited
        # animation has see-through pixels, and measuring that needs an LZW decoder: leave unmeasured.
        "has_transparent_pixels": None if any_transparent else False,
        "has_partial_alpha": None if any_transparent else False, "animated": n > 1, "frame_count": n, "frame_timing": timing,
    }


def parse_jpeg(data: bytes) -> dict:
    pos = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        while data[pos] == 0xFF:
            pos += 1
        marker = data[pos]
        pos += 1
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xD9:
            break
        seg = struct.unpack(">H", data[pos: pos + 2])[0]
        if marker in sof:
            prec, h, w, nf = struct.unpack(">BHHB", data[pos + 2: pos + 8])
            return {
                "format": "jpeg", "width": w, "height": h,
                "color_model": {1: "grayscale", 3: "ycbcr", 4: "cmyk"}.get(nf),
                "bit_depth": prec, "alpha_mode": "none", "has_transparent_pixels": False,
                "has_partial_alpha": False, "animated": False, "frame_count": 1, "frame_timing": None,
            }
        pos += seg
    raise ValueError("JPEG without SOF marker")


def parse_svg(data: bytes) -> dict:
    root = ET.fromstring(data)

    def num(v):
        m = re.fullmatch(r"\s*([0-9.]+)(px)?\s*", v or "")
        if not m:
            return None
        f = float(m.group(1))
        return int(f) if f == int(f) else round(f, 3)

    return {
        "format": "svg", "width": num(root.get("width")), "height": num(root.get("height")),
        "color_model": None, "bit_depth": None, "alpha_mode": "not-measured",
        "has_transparent_pixels": None, "has_partial_alpha": None,
        "animated": False, "frame_count": None, "frame_timing": None,
        "view_box": root.get("viewBox"),
    }


def parse_text(data: bytes) -> dict:
    text = data.decode("utf-8", errors="replace")
    return {
        "format": "lua", "width": None, "height": None, "color_model": None, "bit_depth": None,
        "alpha_mode": "not-applicable", "has_transparent_pixels": None, "has_partial_alpha": None,
        "animated": False, "frame_count": None, "frame_timing": None,
        "line_count": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
    }


def png_alpha_rows(path: Path):
    """Return (width, height, [alpha byte rows]) for an 8-bit non-interlaced RGBA PNG."""
    data = path.read_bytes()
    pos, chunks = 8, []
    while pos < len(data):
        ln, ctype = struct.unpack(">I4s", data[pos: pos + 8])
        chunks.append((ctype, data[pos + 8: pos + 8 + ln]))
        pos += 12 + ln
    w, h, bd, ct, _c, _f, interlace = struct.unpack(">IIBBBBB", next(c for t, c in chunks if t == b"IHDR"))
    if (ct, bd, interlace) != (6, 8, 0):
        raise ValueError("component measurement supports 8-bit non-interlaced RGBA PNG only")
    raw = zlib.decompress(b"".join(c for t, c in chunks if t == b"IDAT"))
    rows = _png_unfilter(raw, h, w * 4, 4)
    return w, h, [bytes(r[3::4]) for r in rows]


def opaque_components(path: Path, alpha_threshold: int = 1, sort_band_px: int = 80) -> list[list[int]]:
    """8-connected components of pixels with alpha >= threshold, as [x, y, w, h] bounds.

    Sorted in reading order: by (vertical band of the component centre, x).
    """
    w, h, rows = png_alpha_rows(path)
    seen = bytearray(w * h)
    out = []
    for y in range(h):
        row = rows[y]
        for x in range(w):
            if row[x] >= alpha_threshold and not seen[y * w + x]:
                stack = [(x, y)]
                seen[y * w + x] = 1
                x0 = x1 = x
                y0 = y1 = y
                while stack:
                    cx, cy = stack.pop()
                    if cx < x0: x0 = cx
                    if cx > x1: x1 = cx
                    if cy < y0: y0 = cy
                    if cy > y1: y1 = cy
                    for ny in (cy - 1, cy, cy + 1):
                        if 0 <= ny < h:
                            nrow = rows[ny]
                            base = ny * w
                            for nx in (cx - 1, cx, cx + 1):
                                if 0 <= nx < w and nrow[nx] >= alpha_threshold and not seen[base + nx]:
                                    seen[base + nx] = 1
                                    stack.append((nx, ny))
                out.append([x0, y0, x1 - x0 + 1, y1 - y0 + 1])
    out.sort(key=lambda b: (int((b[1] + b[3] / 2) // sort_band_px), b[0]))
    return out


def sniff_format(path: Path, data: bytes) -> str:
    if data.startswith(PNG_SIG):
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    ext = path.suffix.lower()
    if ext == ".svg":
        return "svg"
    if ext == ".lua":
        return "lua"
    return "unknown"


def media_facts(path: Path) -> dict:
    """Return the manifest `media` object for a file, plus derived byte count and sha256."""
    data = path.read_bytes()
    fmt = sniff_format(path, data)
    info = {"png": parse_png, "gif": parse_gif, "jpeg": parse_jpeg, "svg": parse_svg, "lua": parse_text}[fmt](data)
    media = OrderedDict()
    media["format"] = fmt
    media["mime"] = MIME[fmt]
    media["extension_matches_format"] = EXT_FORMATS.get(path.suffix.lower()) == fmt
    media["bytes"] = len(data)
    media["width"] = info["width"]
    media["height"] = info["height"]
    if info.get("view_box"):
        media["view_box"] = info["view_box"]
    if info.get("line_count") is not None:
        media["line_count"] = info["line_count"]
    media["color_model"] = info["color_model"]
    media["bit_depth"] = info["bit_depth"]
    media["alpha"] = OrderedDict(
        mode=info["alpha_mode"],
        has_transparent_pixels=info["has_transparent_pixels"],
        has_partial_alpha=info["has_partial_alpha"],
    )
    media["animated"] = info["animated"]
    media["frame_count"] = info["frame_count"]
    media["frame_timing"] = info["frame_timing"]
    return {"sha256": hashlib.sha256(data).hexdigest(), "media": media}


# ----------------------------------------------------------------------------------------
# Documentation scanning
# ----------------------------------------------------------------------------------------

EMBED_RE = re.compile(r"!\[((?:[^\]\\]|\\.)*)\]\(\s*(<[^>]*>|[^)\s]*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
LINK_RE = re.compile(r"\[((?:[^\]\\]|\\.)*)\]\(\s*(<[^>]*>|[^)\s]*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
HTML_RE = re.compile(r"<(img|a|source)\b[^>]*?\b(src|href)\s*=\s*[\"']([^\"']+)[\"']", re.I)
REFDEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
URL_RE = re.compile(r"https?://[^\s<>()\]\"']+")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:|^//")
SOURCE_RE = re.compile(r"^>\s*\*\*Source:\*\*\s*\[[^\]]*\]\(([^)\s]+)\)")


def doc_files() -> list[Path]:
    return [ROOT / "README.md"] + sorted((ROOT / "docs").rglob("*.md"))


def resolve_exact_case(rel_norm: str) -> bool:
    """True if the repo-relative path exists with exactly this letter case (portable check)."""
    cur = ROOT
    for part in rel_norm.split("/"):
        if part in ("", "."):
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return False
        if part not in names:
            return False
        cur = cur / part
    return True


def scan_docs() -> dict:
    """Scan Markdown for asset references.

    Returns {refs: [...], source_urls: {doc: url}, doc_text: {doc: [lines]}}.
    A ref is {doc, line, kind ('embed'|'link'), raw, alt, target (repo-relative or None),
    headings, resolves_exact}.
    """
    refs, source_urls, text = [], {}, {}
    for doc in doc_files():
        rel_doc = doc.relative_to(ROOT).as_posix()
        lines = doc.read_text(encoding="utf-8").splitlines()
        text[rel_doc] = lines
        heads: list[tuple[int, str]] = []
        in_fence = False
        for ln, line in enumerate(lines, 1):
            if re.match(r"^\s*(```|~~~)", line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = SOURCE_RE.match(line)
            if m and ln <= 12:
                source_urls[rel_doc] = m.group(1)
            hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
            if hm:
                lvl = len(hm.group(1))
                heads = [h for h in heads if h[0] < lvl] + [(lvl, hm.group(2))]
            found = []  # (kind, alt, raw)
            work = line
            for m in EMBED_RE.finditer(line):
                found.append(("embed", m.group(1), m.group(2)))
            work = EMBED_RE.sub(lambda m: " " * len(m.group(0)), work)
            for m in LINK_RE.finditer(work):
                found.append(("link", m.group(1), m.group(2)))
            for m in HTML_RE.finditer(line):
                found.append(("embed" if m.group(1).lower() in ("img", "source") else "link", "", m.group(3)))
            m = REFDEF_RE.match(line)
            if m:
                found.append(("link", "", m.group(1)))
            for kind, alt, raw in found:
                raw = raw.strip("<>")
                if not raw or raw.startswith("#") or SCHEME_RE.match(raw):
                    continue
                pth = urllib.parse.unquote(re.split(r"[#?]", raw)[0])
                if not pth:
                    continue
                joined = os.path.normpath(os.path.join(os.path.dirname(rel_doc), pth)).replace(os.sep, "/")
                image_like = pth.lower().endswith(IMG_EXTS) or ASSET_ROOT in joined.split("/")
                if not image_like:
                    continue
                escapes = joined.startswith("../") or joined == ".."
                refs.append({
                    "doc": rel_doc, "line": ln, "kind": kind, "raw": raw, "alt": alt,
                    "target": None if escapes else joined,
                    "headings": " > ".join(h[1] for h in heads),
                    "resolves_exact": (not escapes) and resolve_exact_case(joined),
                })
    return {"refs": refs, "source_urls": source_urls, "text": text}


def mention_refs(scan: dict, assets: dict[str, str]) -> dict[str, list[dict]]:
    """Find non-path textual mentions: exact filename in prose, or in an external URL.

    assets: {repo-relative path: basename}. Alt text and local-path targets are excluded.
    """
    out: dict[str, list[dict]] = defaultdict(list)
    pats = {
        p: re.compile(r"(?<![\w.\-/])" + re.escape(b) + r"(?![\w\-]|\.(?:png|gif|svg|lua)\b)")
        for p, b in assets.items()
    }
    for doc, lines in scan["text"].items():
        joined = "\n".join(lines)
        in_fence = False
        headings_at: list[tuple[int, str]] = []
        for ln, line in enumerate(lines, 1):
            if re.match(r"^\s*(```|~~~)", line):
                in_fence = not in_fence
                continue
            hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line) if not in_fence else None
            if hm:
                lvl = len(hm.group(1))
                headings_at = [h for h in headings_at if h[0] < lvl] + [(lvl, hm.group(2))]
            if in_fence:
                continue
            urls = URL_RE.findall(line)
            stripped = EMBED_RE.sub(" ", line)
            stripped = LINK_RE.sub(lambda m: " " if not SCHEME_RE.match(m.group(2).strip("<>")) else m.group(0), stripped)
            stripped = HTML_RE.sub(" ", stripped)
            heading = " > ".join(h[1] for h in headings_at)
            for url in urls:
                last = urllib.parse.unquote(re.split(r"[#?]", url)[0].rstrip("/").split("/")[-1])
                last = re.sub(r"^File:", "", last)
                for path, base in assets.items():
                    if last == base:
                        out[path].append({"doc": doc, "line": ln, "kind": "external-citation", "url": url, "headings": heading})
            no_urls = URL_RE.sub(" ", stripped)
            for path, base in assets.items():
                if base in no_urls and pats[path].search(no_urls):
                    out[path].append({"doc": doc, "line": ln, "kind": "filename-mention", "headings": heading})
    return out


def build_related_docs(path: str, scan: dict, mentions: dict) -> list[dict]:
    """Group raw refs/mentions for one asset into manifest `related_docs` entries."""
    groups: dict[tuple[str, str], dict] = OrderedDict()

    def add(doc, kind, line, heading, alt=None, url=None):
        g = groups.setdefault((doc, kind), {"path": doc, "reference": kind, "lines": [], "headings": [], "alt_texts": [], "urls": []})
        g["lines"].append(line)
        if heading and heading not in g["headings"]:
            g["headings"].append(heading)
        if alt and alt not in g["alt_texts"]:
            g["alt_texts"].append(alt)
        if url and url not in g["urls"]:
            g["urls"].append(url)

    for r in scan["refs"]:
        if r["target"] == path:
            add(r["doc"], "embedded-image" if r["kind"] == "embed" else "link", r["line"], r["headings"], alt=r["alt"])
    for m in mentions.get(path, []):
        add(m["doc"], m["kind"], m["line"], m["headings"], url=m.get("url"))
    out = []
    for key in sorted(groups, key=lambda k: (k[0], k[1])):
        g = groups[key]
        entry = OrderedDict(path=g["path"], reference=g["reference"], lines=sorted(set(g["lines"])), headings=g["headings"])
        if g["alt_texts"]:
            entry["alt_texts"] = g["alt_texts"]
        if g["urls"]:
            entry["urls"] = g["urls"]
        out.append(entry)
    return out


# ----------------------------------------------------------------------------------------
# Manifest helpers
# ----------------------------------------------------------------------------------------

def list_asset_files() -> list[str]:
    base = ROOT / ASSET_ROOT
    return sorted(p.relative_to(ROOT).as_posix() for p in base.rglob("*") if p.is_file() or p.is_symlink())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def order_entry(e: dict) -> dict:
    out = OrderedDict()
    for k in ENTRY_ORDER:
        if k in e:
            out[k] = e[k]
    for k in e:
        if k not in out:
            out[k] = e[k]
    if isinstance(out.get("provenance"), dict):
        p = out["provenance"]
        po = OrderedDict((k, p[k]) for k in PROVENANCE_ORDER if k in p)
        po.update((k, v) for k, v in p.items() if k not in po)
        out["provenance"] = po
    return out


def dump_manifest(m: dict) -> str:
    m = dict(m)
    m["assets"] = [order_entry(e) for e in m["assets"]]
    text = json.dumps(m, indent=2, ensure_ascii=False)
    # keep arrays of plain numbers on one line so pixel bounds and frame lists stay readable
    text = re.sub(r"\[\s*(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)*)\s*\]",
                  lambda mo: "[" + re.sub(r"\s*,\s*", ", ", mo.group(1)) + "]", text)
    return text + "\n"


def pick_canonical(members: list[str], referenced: set[str]) -> str:
    """Deterministic canonical member of an exact-duplicate group."""
    return sorted(members, key=lambda p: (p not in referenced, " " in p, p))[0]


def derive_all(manifest: dict) -> dict:
    """Compute every derived field from the filesystem + docs. Returns {path: derived-dict}."""
    scan = scan_docs()
    entries = {e["path"]: e for e in manifest["assets"]}
    files = list_asset_files()
    facts = {p: media_facts(ROOT / p) for p in files}
    mentions = mention_refs(scan, {p: os.path.basename(p) for p in files})
    referenced = {r["target"] for r in scan["refs"] if r["target"]}
    by_hash: dict[str, list[str]] = defaultdict(list)
    for p, f in facts.items():
        by_hash[f["sha256"]].append(p)
    id_of = {p: entries[p]["id"] for p in entries}
    derived = {}
    for p in files:
        rd = build_related_docs(p, scan, mentions)
        pages = sorted({scan["source_urls"][d["path"]] for d in rd
                        if d["reference"] in ("embedded-image", "link") and d["path"] in scan["source_urls"]})
        group = by_hash[facts[p]["sha256"]]
        dup_of, dups = None, []
        if len(group) > 1 and all(g in id_of for g in group):
            canon = pick_canonical(group, referenced)
            if p == canon:
                dups = sorted(id_of[g] for g in group if g != canon)
            else:
                dup_of = id_of[canon]
        derived[p] = {**facts[p], "related_docs": rd, "source_pages": pages,
                      "exact_duplicate_of": dup_of, "exact_duplicates": dups}
    return {"derived": derived, "scan": scan, "mentions": mentions, "referenced": referenced}


def apply_derived(entry: dict, d: dict) -> None:
    entry["sha256"] = d["sha256"]
    entry["media"] = d["media"]
    entry["related_docs"] = d["related_docs"]
    prov = entry.setdefault("provenance", OrderedDict())
    prov["source_pages"] = d["source_pages"]
    rel = entry.setdefault("relationships", OrderedDict())
    rel["exact_duplicate_of"] = d["exact_duplicate_of"]
    rel["exact_duplicates"] = d["exact_duplicates"]
    rel.setdefault("related", [])


def stub_entry(path: str) -> dict:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(path).stem.lower()).strip("-")
    return {
        "id": f"unreviewed.{stem}", "path": path, "kind": "other",
        "summary": "UNREVIEWED: new file detected by sync; not yet described.",
        "depicts": ["unreviewed"],
        "demonstrates": [{"claim": "unreviewed", "basis": "inferred"}],
        "runtime_role": "unknown", "runtime_role_rationale": "Not yet reviewed.",
        "implementation_notes": ["Not yet reviewed."],
        "provenance": {"cited_source_url": None, "cited_source_evidence": None,
                       "acquisition": {"method": "unknown", "evidence": "Not yet reviewed."},
                       "creator": None, "creator_evidence": None, "license": None, "license_evidence": None,
                       "rights_status": "unknown", "rights_notes": "Not yet reviewed."},
        "verification": {"visual_inspection": "none", "inspected_frames": [], "numeric_spatial_metadata": "not-recorded"},
        "confidence": {"level": "low", "reason": "New file; no review performed.", "needs_review": True,
                       "review_flags": ["description-uncertain", "provenance-unverified", "rights-unverified"]},
    }


# ----------------------------------------------------------------------------------------
# Minimal JSON Schema (draft 2020-12 subset) validator - fail-closed on unknown keywords
# ----------------------------------------------------------------------------------------

_ANNOTATIONS = {"$schema", "$id", "$comment", "$defs", "title", "description", "default", "examples"}
_KNOWN = {
    "type", "enum", "const", "properties", "required", "additionalProperties", "items", "minItems",
    "maxItems", "minLength", "maxLength", "pattern", "minimum", "maximum", "uniqueItems", "$ref",
    "oneOf", "anyOf", "allOf", "if", "then", "else",
}


def _type_ok(v, t) -> bool:
    if isinstance(t, list):
        return any(_type_ok(v, x) for x in t)
    return {
        "string": isinstance(v, str), "integer": isinstance(v, int) and not isinstance(v, bool),
        "number": isinstance(v, (int, float)) and not isinstance(v, bool), "boolean": isinstance(v, bool),
        "null": v is None, "array": isinstance(v, list), "object": isinstance(v, dict),
    }[t]


def schema_validate(inst, schema, root, where="$") -> list[str]:
    errs: list[str] = []
    for k in schema:
        if k not in _KNOWN and k not in _ANNOTATIONS and not k.startswith("x-"):
            errs.append(f"{where}: validator does not support schema keyword {k!r}")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            return errs + [f"{where}: only local $ref supported"]
        node = root
        for part in ref[2:].split("/"):
            node = node[part]
        errs += schema_validate(inst, node, root, where)
    if "type" in schema and not _type_ok(inst, schema["type"]):
        return errs + [f"{where}: expected {schema['type']}, got {type(inst).__name__}"]
    if "const" in schema and inst != schema["const"]:
        errs.append(f"{where}: expected const {schema['const']!r}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{where}: {inst!r} not in {schema['enum']}")
    if isinstance(inst, str):
        if "minLength" in schema and len(inst.strip()) < schema["minLength"]:
            errs.append(f"{where}: string shorter than {schema['minLength']} (after trimming)")
        if "maxLength" in schema and len(inst) > schema["maxLength"]:
            errs.append(f"{where}: string longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append(f"{where}: {inst!r} does not match {schema['pattern']}")
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append(f"{where}: {inst} < minimum {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append(f"{where}: {inst} > maximum {schema['maximum']}")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errs.append(f"{where}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            errs.append(f"{where}: more than {schema['maxItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in inst}) != len(inst):
            errs.append(f"{where}: items not unique")
        if "items" in schema:
            for i, x in enumerate(inst):
                errs += schema_validate(x, schema["items"], root, f"{where}[{i}]")
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        for r in schema.get("required", []):
            if r not in inst:
                errs.append(f"{where}: missing required property {r!r}")
        for k, v in inst.items():
            if k in props:
                errs += schema_validate(v, props[k], root, f"{where}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{where}: unexpected property {k!r}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += schema_validate(v, schema["additionalProperties"], root, f"{where}.{k}")
    for sub in schema.get("allOf", []):
        errs += schema_validate(inst, sub, root, where)
    if "anyOf" in schema and not any(not schema_validate(inst, s, root, where) for s in schema["anyOf"]):
        errs.append(f"{where}: matches none of anyOf")
    if "oneOf" in schema:
        n = sum(1 for s in schema["oneOf"] if not schema_validate(inst, s, root, where))
        if n != 1:
            errs.append(f"{where}: matches {n} of oneOf (expected exactly 1)")
    if "if" in schema:
        if not schema_validate(inst, schema["if"], root, where):
            if "then" in schema:
                errs += schema_validate(inst, schema["then"], root, where)
        elif "else" in schema:
            errs += schema_validate(inst, schema["else"], root, where)
    return errs


# ----------------------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------------------

def cmd_facts(args) -> int:
    for f in args.files:
        p = Path(f).resolve()
        print(json.dumps({p.relative_to(ROOT).as_posix(): media_facts(p)}, indent=1))
    return 0


def cmd_sync(args) -> int:
    manifest = load_json(Path(args.manifest))
    entries = {e["path"]: e for e in manifest["assets"]}
    files = list_asset_files()
    added = [p for p in files if p not in entries]
    for p in added:
        e = stub_entry(p)
        manifest["assets"].append(e)
        entries[p] = e
    manifest["assets"].sort(key=lambda e: e["path"])
    result = derive_all(manifest)
    for p, e in entries.items():
        if p in result["derived"]:
            apply_derived(e, result["derived"][p])
    text = dump_manifest(manifest)
    changed = text != Path(args.manifest).read_text(encoding="utf-8")
    if not args.dry_run and changed:
        Path(args.manifest).write_text(text, encoding="utf-8")
    missing = [p for p in entries if p not in result["derived"]]
    print(f"sync: {len(files)} files, {len(added)} stub(s) added, {len(missing)} entry/entries with missing file, "
          f"manifest {'would change' if changed and args.dry_run else 'updated' if changed else 'unchanged'}")
    return 0


class Checker:
    def __init__(self):
        self.failures: list[str] = []
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, errors: list[str]) -> None:
        ok = not errors
        self.results.append((name, ok, "" if ok else f"{len(errors)} problem(s)"))
        for e in errors[:25]:
            self.failures.append(f"[{name}] {e}")
        if len(errors) > 25:
            self.failures.append(f"[{name}] ... and {len(errors) - 25} more")


PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum|UNREVIEWED)\b", re.I)


def walk_strings(node, where="$"):
    if isinstance(node, str):
        yield where, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{where}[{i}]")


def git_originals_unchanged() -> tuple[bool | None, str]:
    try:
        top = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if top.returncode != 0:
            return None, "not a git repository; skipped"
        st = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", ASSET_ROOT], capture_output=True, text=True)
        df = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", ASSET_ROOT], capture_output=True)
        if st.stdout.strip() or df.returncode != 0:
            return False, (st.stdout.strip() or "diff against HEAD is non-empty")
        return True, "images/ identical to HEAD; no untracked/modified files"
    except FileNotFoundError:
        return None, "git not installed; skipped"


def cmd_validate(args) -> int:
    ck = Checker()
    manifest = load_json(Path(args.manifest))
    schema = load_json(Path(args.schema))
    assets = manifest.get("assets", [])

    # 1. schema itself + stack neutrality
    s_err = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        s_err.append("schema must declare draft 2020-12")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(schema.get("version", schema.get("x-schema-version", "")))):
        s_err.append("schema needs a semver 'x-schema-version'")
    if schema.get("x-schema-version") != manifest.get("schema_version"):
        s_err.append(f"manifest schema_version {manifest.get('schema_version')!r} != schema x-schema-version {schema.get('x-schema-version')!r}")
    ck.check("schema is versioned and matches manifest", s_err)
    blob = json.dumps(schema).lower()
    hits = [t for t in FORBIDDEN_SCHEMA_TERMS if re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", blob)]
    ck.check("schema has no framework-specific terms", [f"forbidden term in schema: {t}" for t in hits])

    # 2. schema validity of the manifest
    ck.check("manifest conforms to JSON Schema", schema_validate(manifest, schema, schema))

    # 3. inventory
    files = list_asset_files()
    paths = [a.get("path") for a in assets]
    c = Counter(paths)
    inv = [f"duplicate manifest entries for {p}" for p, n in c.items() if n > 1]
    inv += [f"file without manifest entry: {p}" for p in files if p not in c]
    inv += [f"manifest entry without file: {p}" for p in c if p not in files]
    inv += [f"path differs only by case: {p}" for p in c if sum(1 for q in c if q.lower() == p.lower()) > 1]
    ck.check(f"every images/ file has exactly one manifest entry ({len(files)} files / {len(assets)} entries)", inv)
    ck.check("every manifest path exists with exact letter case",
             [f"{p}" for p in c if not (ROOT / p).is_file() or not resolve_exact_case(p)])
    ck.check("paths are repository-relative under images/",
             [p for p in c if p.startswith("/") or ".." in p.split("/") or not p.startswith(ASSET_ROOT + "/")])
    ids = Counter(a.get("id") for a in assets)
    ck.check("ids are unique", [f"duplicate id {i}" for i, n in ids.items() if n > 1])

    # 4. hashes + derived facts
    derived_state = derive_all(manifest) if not inv else None
    if derived_state:
        d = derived_state["derived"]
        ck.check("recorded SHA-256 matches file bytes", [p for a in assets for p in [a["path"]] if a.get("sha256") != d[p]["sha256"]])
        ck.check("media facts match re-parsed file headers", [
            f"{a['path']}: media differs from re-parsed facts" for a in assets if json.loads(json.dumps(a.get("media"))) != json.loads(json.dumps(d[a["path"]]["media"]))])
        ck.check("files whose content type disagrees with extension are flagged for review", [
            f"{a['path']}: content is {a['media']['format']} but extension says otherwise; needs review flag format-extension-mismatch"
            for a in assets if not a["media"]["extension_matches_format"] and "format-extension-mismatch" not in a["confidence"]["review_flags"]])
        ck.check("related_docs matches a fresh scan of the Markdown", [
            f"{a['path']}: related_docs is stale (run sync)" for a in assets
            if json.loads(json.dumps(a.get("related_docs"))) != json.loads(json.dumps(d[a["path"]]["related_docs"]))])
        dup_err = []
        by_hash: dict[str, list[dict]] = defaultdict(list)
        for a in assets:
            by_hash[d[a["path"]]["sha256"]].append(a)
        idmap = {a["id"]: a for a in assets}
        for h, grp in by_hash.items():
            gids = {a["id"] for a in grp}
            if len(grp) == 1:
                a = grp[0]
                if a["relationships"].get("exact_duplicate_of") or a["relationships"].get("exact_duplicates"):
                    dup_err.append(f"{a['id']} claims duplicates but is unique by hash")
                continue
            canon = [a for a in grp if a["relationships"].get("exact_duplicate_of") is None]
            if len(canon) != 1:
                dup_err.append(f"group {h[:12]}: expected exactly 1 canonical entry, found {len(canon)}")
                continue
            c0 = canon[0]
            if set(c0["relationships"]["exact_duplicates"]) != gids - {c0["id"]}:
                dup_err.append(f"group {h[:12]}: canonical {c0['id']} exact_duplicates mismatch")
            for a in grp:
                if a is not c0 and (a["relationships"]["exact_duplicate_of"] != c0["id"] or a["relationships"]["exact_duplicates"]):
                    dup_err.append(f"group {h[:12]}: {a['id']} inconsistent duplicate pointers")
        ck.check("exact-duplicate groups are internally consistent", dup_err)
        # relationships
        rel_err = []
        inverse = {"transparent-counterpart-of": "chroma-key-counterpart-of", "chroma-key-counterpart-of": "transparent-counterpart-of",
                   "companion-of": "companion-of", "same-mechanic-as": "same-mechanic-as", "visual-variant-of": "visual-variant-of"}
        for a in assets:
            for r in a["relationships"]["related"]:
                t = idmap.get(r["target"])
                if t is None:
                    rel_err.append(f"{a['id']}: relation target {r['target']} does not exist")
                    continue
                if r["target"] == a["id"]:
                    rel_err.append(f"{a['id']}: self relation")
                inv_t = inverse.get(r["type"])
                if inv_t and not any(x["type"] == inv_t and x["target"] == a["id"] for x in t["relationships"]["related"]):
                    rel_err.append(f"{a['id']} --{r['type']}--> {t['id']} lacks reciprocal {inv_t}")
            if a["relationships"].get("exact_duplicate_of") in (a["id"],):
                rel_err.append(f"{a['id']}: duplicate of itself")
        ck.check("relationship targets exist and symmetric types are reciprocal", rel_err)

        # doc references resolve
        scan = derived_state["scan"]
        bad = []
        for r in scan["refs"]:
            if r["target"] is None:
                bad.append(f"{r['doc']}:{r['line']} escapes repository: {r['raw']}")
            elif not r["resolves_exact"]:
                bad.append(f"{r['doc']}:{r['line']} does not resolve (missing or wrong letter case): {r['raw']}")
        n_refs = len(scan["refs"])
        ck.check(f"documentation asset references resolve, case-exact ({n_refs} references)", bad)

        # cited URLs actually appear in docs
        all_text = "\n".join("\n".join(v) for v in scan["text"].values())
        url_err = []
        for a in assets:
            u = a["provenance"].get("cited_source_url")
            if u and u not in all_text:
                url_err.append(f"{a['id']}: cited_source_url not found in any Markdown file: {u}")
        ck.check("every cited_source_url appears verbatim in repository docs", url_err)

    # 5. semantic completeness
    sem = []
    for a in assets:
        for where, s in walk_strings(a):
            if PLACEHOLDER_RE.search(s):
                sem.append(f"{a.get('id')}{where[1:]}: placeholder text {s[:40]!r}")
            if s != s.strip() or (s == "" ):
                sem.append(f"{a.get('id')}{where[1:]}: empty/untrimmed string")
    ck.check("no placeholder, empty, or untrimmed text in any entry", sem)

    rules = []
    for a in assets:
        i, k, rr = a["id"], a["kind"], a["runtime_role"]
        prov, conf = a["provenance"], a["confidence"]
        if prov["rights_status"] == "explicit-license" and not (prov.get("license") and prov.get("license_evidence")):
            rules.append(f"{i}: rights_status explicit-license needs license + license_evidence")
        if prov.get("license") and prov["rights_status"] != "explicit-license":
            rules.append(f"{i}: license recorded but rights_status is {prov['rights_status']}")
        if prov["rights_status"] != "explicit-license" and "rights-unverified" not in conf["review_flags"]:
            rules.append(f"{i}: unknown/unclear rights must carry review flag rights-unverified")
        if not prov.get("cited_source_url") and "provenance-unverified" not in conf["review_flags"]:
            rules.append(f"{i}: no cited_source_url; must carry review flag provenance-unverified")
        if conf["level"] == "low" and not conf["needs_review"]:
            rules.append(f"{i}: low confidence requires needs_review=true")
        if conf["needs_review"] and not conf["review_flags"]:
            rules.append(f"{i}: needs_review=true requires at least one review flag")
        if rr == "candidate-runtime-art" and k not in ("sprite-atlas", "control-ui-icon"):
            rules.append(f"{i}: kind {k} may not be candidate-runtime-art")
        if k == "map-composite" and rr == "source-data":
            rules.append(f"{i}: map composites must not be classified as source-data")
        if k in ("collision-diagram", "mechanic-demonstration", "mechanic-diagram", "object-hitbox-reference",
                 "terrain-height-mask-reference", "map-composite") and rr in ("candidate-runtime-art", "source-data"):
            rules.append(f"{i}: documentation diagram/capture kind {k} classified as {rr}")
        if a["media"]["animated"] and "sequence" not in a:
            rules.append(f"{i}: animated asset needs a sequence description")
        if not a["media"]["animated"] and "sequence" in a:
            rules.append(f"{i}: static asset must not have a sequence")
        if k == "sprite-atlas" and "atlas" not in a:
            rules.append(f"{i}: sprite-atlas needs an atlas block")
        if "atlas" in a:
            at = a["atlas"]
            fr = at["frame_regions"]
            if fr["status"] == "verified" and at["status"] == "requires-manual-review":
                rules.append(f"{i}: frame regions verified but atlas status is requires-manual-review")
            if fr["status"] == "verified" and not fr.get("regions"):
                rules.append(f"{i}: verified frame_regions must list regions")
            if fr["status"] != "verified" and (fr.get("regions") or fr.get("non_sprite_components")):
                rules.append(f"{i}: unverified frame_regions must not list regions")
            if at["status"] != "verified" and not {"atlas-frame-boundaries", "atlas-pivots", "atlas-pose-names"} & set(conf["review_flags"]):
                rules.append(f"{i}: atlas not fully verified must carry an atlas-* review flag")
            unresolved = [k for k in ("poses", "pivot", "mirroring", "animation_sequences", "frame_durations", "loop_behavior", "collision_relation") if at[k]["status"] not in ("verified", "not-applicable")]
            if at["status"] == "verified" and unresolved:
                rules.append(f"{i}: atlas status verified but unresolved properties: {unresolved}")
            for r in fr.get("regions", []) + fr.get("non_sprite_components", []):
                if r[0] + r[2] > a["media"]["width"] or r[1] + r[3] > a["media"]["height"]:
                    rules.append(f"{i}: frame region {r} exceeds image bounds")
        if a["verification"]["numeric_spatial_metadata"] == "labels-transcribed-unverified" and "numeric-values-unverified" not in conf["review_flags"]:
            rules.append(f"{i}: transcribed numeric labels must carry review flag numeric-values-unverified")
        if not a["media"]["animated"] and a["verification"]["inspected_frames"]:
            rules.append(f"{i}: static asset lists inspected_frames")
        fc = a["media"]["frame_count"]
        if "sequence" in a:
            for t in a["sequence"]["transitions"]:
                if not (1 <= t["at_frame"] <= fc):
                    rules.append(f"{i}: transition at_frame {t['at_frame']} outside 1..{fc}")
                elif t["at_frame"] not in a["verification"]["inspected_frames"]:
                    rules.append(f"{i}: transition cites frame {t['at_frame']} which was not inspected")
        for fr in a["verification"]["inspected_frames"]:
            if fc is None or not (1 <= fr <= fc):
                rules.append(f"{i}: inspected frame {fr} outside 1..{fc}")
        if a["media"]["animated"] and a["verification"]["visual_inspection"] == "full-static" :
            rules.append(f"{i}: animated asset cannot be full-static inspected")
    ck.check("semantic consistency rules (kind/role/rights/atlas/sequence/confidence)", rules)

    # 5b. verified atlas regions are reproducible from pixels
    at_err = []
    for a in assets:
        fr = a.get("atlas", {}).get("frame_regions", {})
        if fr.get("status") == "verified" and fr.get("method") == "opaque-component-bounds":
            got = opaque_components(ROOT / a["path"], fr["alpha_threshold"], fr["sort_band_px"])
            want = sorted(fr["regions"] + fr.get("non_sprite_components", []), key=lambda b: (int((b[1] + b[3] / 2) // fr["sort_band_px"]), b[0]))
            if got != want:
                at_err.append(f"{a['id']}: recorded regions differ from a fresh measurement ({len(want)} recorded, {len(got)} measured)")
            elif fr["regions"] != sorted(fr["regions"], key=lambda b: (int((b[1] + b[3] / 2) // fr["sort_band_px"]), b[0])):
                at_err.append(f"{a['id']}: regions are not in the documented reading order")
    ck.check("verified atlas frame regions are reproduced by re-measuring the pixels", at_err)

    # 6. originals unchanged
    ok, msg = git_originals_unchanged()
    if ok is None:
        ck.results.append(("original assets unchanged vs git HEAD", True, f"SKIPPED ({msg})"))
    else:
        ck.check("original assets unchanged vs git HEAD", [] if ok else [msg])
        if ok:
            ck.results[-1] = (ck.results[-1][0], True, msg)

    # 7. report freshness
    if not ck.failures and not args.no_report_check:
        fresh = render_report(manifest, derived_state)
        ck.check("catalog/REVIEW.md is up to date", [] if REVIEW.exists() and REVIEW.read_text(encoding="utf-8") == fresh else ["REVIEW.md is stale (run: python3 scripts/catalog.py report)"])

    width = max(len(n) for n, _, _ in ck.results)
    for name, ok, note in ck.results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  - ' + note) if note else ''}")
    for f in ck.failures:
        print("    " + f)
    good = all(ok for _, ok, _ in ck.results)
    print(f"\nvalidate: {'OK' if good else 'FAILED'} ({sum(1 for _, o, _ in ck.results if o)}/{len(ck.results)} checks passed)")
    return 0 if good else 1


# ----------------------------------------------------------------------------------------
# Review report
# ----------------------------------------------------------------------------------------

def _bullets(items, fmt=lambda x: x):
    return "\n".join(f"- {fmt(i)}" for i in items) if items else "_None._"


def render_report(manifest: dict, state: dict | None = None) -> str:
    if state is None:
        state = derive_all(manifest)
    scan = state["scan"]
    A = manifest["assets"]
    by_id = {a["id"]: a for a in A}
    fmt_count = Counter(a["media"]["format"] for a in A)
    ext_count = Counter(Path(a["path"]).suffix for a in A)
    kind_count = Counter(a["kind"] for a in A)
    role_count = Counter(a["runtime_role"] for a in A)
    rights_count = Counter(a["provenance"]["rights_status"] for a in A)
    conf_count = Counter(a["confidence"]["level"] for a in A)
    L: list[str] = []
    w = L.append
    w("# Asset Catalog Review Report")
    w("")
    w("> Generated by `python3 scripts/catalog.py report` from `catalog/asset-manifest.json`. Do not edit by hand.")
    w(f"> Catalog date: {manifest['catalog']['catalog_date']} · Schema {manifest['schema_version']}")
    w("")
    w("## 1. Inventory totals")
    w("")
    w(f"- Regular files under `images/`: **{len(A)}** (manifest entries: {len(A)})")
    w(f"- Total bytes: {sum(a['media']['bytes'] for a in A):,}")
    animated = [a for a in A if a["media"]["animated"]]
    w(f"- Animated: {len(animated)} (all GIF; total frames {sum(a['media']['frame_count'] for a in animated):,})")
    w("")
    w("| Format | Files |")
    w("| --- | ---: |")
    for k, v in sorted(fmt_count.items()):
        w(f"| {k} | {v} |")
    upper = sorted(a["path"] for a in A if Path(a["path"]).suffix != Path(a["path"]).suffix.lower())
    w("")
    w(f"Extension case: {', '.join(f'`{k}` ×{v}' for k, v in sorted(ext_count.items()))}. "
      f"{len(upper)} file(s) use a non-lowercase extension and are referenced case-exactly by docs where referenced: "
      + ", ".join(f"`{u}`" for u in upper) + ".")
    w("")
    w("| Semantic kind | Files |")
    w("| --- | ---: |")
    for k, v in sorted(kind_count.items(), key=lambda kv: (-kv[1], kv[0])):
        w(f"| {k} | {v} |")
    w("")
    w("| Runtime role | Files |")
    w("| --- | ---: |")
    for k, v in sorted(role_count.items(), key=lambda kv: (-kv[1], kv[0])):
        w(f"| {k} | {v} |")
    w("")
    w("| Rights status | Files |")
    w("| --- | ---: |")
    for k, v in sorted(rights_count.items(), key=lambda kv: (-kv[1], kv[0])):
        w(f"| {k} | {v} |")
    w("")
    w("| Confidence | Files |")
    w("| --- | ---: |")
    for k in ("high", "medium", "low"):
        w(f"| {k} | {conf_count.get(k, 0)} |")
    w("")

    # 2. duplicates
    w("## 2. Exact binary duplicates")
    w("")
    canon = [a for a in A if a["relationships"]["exact_duplicates"]]
    n_dup_files = sum(len(a["relationships"]["exact_duplicates"]) for a in canon)
    w(f"**{len(canon)}** duplicate groups; **{n_dup_files}** redundant files (identical SHA-256).")
    w("")
    for a in canon:
        w(f"- `{a['sha256'][:16]}…` canonical `{a['path']}` (`{a['id']}`)")
        for d in a["relationships"]["exact_duplicates"]:
            b = by_id[d]
            refs = [r for r in b["related_docs"] if r["reference"] in ("embedded-image", "link")]
            note = "no local-path reference" if not refs else f"referenced from {len(refs)} doc(s)"
            alts = sorted({t for r in b["related_docs"] for t in r.get("alt_texts", [])})
            w(f"  - duplicate `{b['path']}` (`{b['id']}`) - {note}")
        alt_hits = sorted({t for r in a["related_docs"] for t in r.get("alt_texts", []) if " " in t and t.lower().endswith(Path(a["path"]).suffix.lower())})
        for t in alt_hits:
            w(f"  - doc alt text `{t}` names the space-form filename while the link target is `{a['path']}`")
    w("")
    w("Likely semantic/filename variants (not byte-identical) are recorded per entry under `relationships.related`:")
    w("")
    rel_rows = []
    for a in A:
        for r in a["relationships"]["related"]:
            if r["type"] in ("visual-variant-of", "transparent-counterpart-of", "chroma-key-counterpart-of", "derived-from"):
                rel_rows.append((a["path"], r["type"], by_id[r["target"]]["path"], r.get("basis", "")))
    w(_bullets(rel_rows, lambda r: f"`{r[0]}` — {r[1]} → `{r[2]}` ({r[3]})"))
    w("")

    # 3. orphans
    w("## 3. Unreferenced / orphaned assets")
    w("")
    w("An asset is **orphaned** when no Markdown file embeds or links it by a local path. "
      "Textual mentions and external-URL citations are reported separately.")
    w("")
    orphans = [a for a in A if not any(r["reference"] in ("embedded-image", "link") for r in a["related_docs"])]
    w(f"**{len(orphans)}** orphaned of {len(A)}; {len(A) - len(orphans)} referenced by local path.")
    w("")
    for a in orphans:
        cites = [r for r in a["related_docs"] if r["reference"] in ("external-citation", "filename-mention")]
        dup = a["relationships"]["exact_duplicate_of"]
        if cites:
            why = "; ".join(f"{r['reference']} in `{r['path']}` (lines {', '.join(map(str, r['lines']))})" for r in cites)
        elif dup:
            why = f"byte-identical duplicate of `{by_id[dup]['path']}`, which is the referenced copy"
        else:
            why = "no reference or mention of any kind in repository Markdown"
        w(f"- `{a['path']}` — {why}")
    w("")

    # 4. provenance
    w("## 4. Missing provenance and rights information")
    w("")
    no_url = [a for a in A if not a["provenance"]["cited_source_url"]]
    w(f"- No per-file cited source URL: **{len(no_url)}** of {len(A)}. Entries with one: "
      + ", ".join(f"`{a['path']}`" for a in A if a["provenance"]["cited_source_url"]) + ".")
    w(f"- No named creator: **{sum(1 for a in A if not a['provenance']['creator'])}** of {len(A)}.")
    w(f"- No explicit license: **{sum(1 for a in A if not a['provenance']['license'])}** of {len(A)}.")
    w(f"- Rights status `unknown`: **{rights_count.get('unknown', 0)}**; `restricted-or-unclear`: **{rights_count.get('restricted-or-unclear', 0)}**; "
      f"`explicit-license`: **{rights_count.get('explicit-license', 0)}**.")
    acq = Counter(a["provenance"]["acquisition"]["method"] for a in A)
    w("- Acquisition method: " + ", ".join(f"{k} ×{v}" for k, v in sorted(acq.items())) + ".")
    w("")
    w("Entries whose acquisition or origin is **not** the wiki scraper (highest-priority provenance gaps):")
    w("")
    w(_bullets([a for a in A if a["provenance"]["acquisition"]["method"] != "scraped-from-wiki"],
               lambda a: f"`{a['path']}` — {a['provenance']['acquisition']['method']}: {a['provenance']['acquisition']['evidence']}"))
    w("")

    # 5. low confidence
    w("## 5. Low-confidence and manual-review entries")
    w("")
    low = [a for a in A if a["confidence"]["level"] == "low"]
    med = [a for a in A if a["confidence"]["level"] == "medium"]
    review = [a for a in A if a["confidence"]["needs_review"]]
    w(f"- Low confidence: **{len(low)}**; medium: **{len(med)}**; flagged `needs_review`: **{len(review)}**.")
    w("")
    w("### Low confidence")
    w("")
    w(_bullets(low, lambda a: f"`{a['path']}` — {a['confidence']['reason']}"))
    w("")
    w("### Medium confidence")
    w("")
    w(_bullets(med, lambda a: f"`{a['path']}` — {a['confidence']['reason']}"))
    w("")
    w("### Review flag frequency (excluding blanket provenance/rights flags)")
    w("")
    flags = Counter(f for a in A for f in a["confidence"]["review_flags"] if f not in ("provenance-unverified", "rights-unverified"))
    w(_bullets(sorted(flags.items()), lambda kv: f"`{kv[0]}` ×{kv[1]}"))
    w("")

    # 6. atlas work
    w("## 6. Assets requiring atlas / frame-boundary work")
    w("")
    atl = [a for a in A if "atlas" in a]
    for a in atl:
        at = a["atlas"]
        w(f"### `{a['path']}` — atlas status: **{at['status']}**")
        w("")
        for key in ("frame_regions", "poses", "animation_sequences", "frame_durations", "loop_behavior", "mirroring", "pivot", "collision_relation"):
            v = at[key]
            w(f"- `{key}`: {v['status']}" + (f" — {v['note']}" if v.get("note") else ""))
        if at.get("review_notes"):
            w("")
            for n in at["review_notes"]:
                w(f"  - {n}")
        w("")
    other = [a for a in A if "atlas-frame-boundaries" in a["confidence"]["review_flags"] and "atlas" not in a]
    if other:
        w("Other assets flagged for frame-boundary work:")
        w("")
        w(_bullets(other, lambda a: f"`{a['path']}`"))
        w("")

    # 7. unresolved docs refs
    w("## 7. Documentation references that do not resolve")
    w("")
    bad = [r for r in scan["refs"] if r["target"] is None or not r["resolves_exact"]]
    n_refs = len(scan["refs"])
    w(f"Scanned `README.md` and {len(scan['text']) - 1} files under `docs/`: **{n_refs}** local image/asset references "
      f"(embedded and linked, outside code fences); **{len(bad)}** unresolved (missing file or wrong letter case).")
    w("")
    w(_bullets(bad, lambda r: f"`{r['doc']}:{r['line']}` → `{r['raw']}`"))
    w("")
    w("Reference anomalies that resolve but are worth knowing:")
    w("")
    anomalies = []
    for a in A:
        for r in a["related_docs"]:
            for t in r.get("alt_texts", []):
                if t.endswith(Path(a["path"]).suffix) and t != os.path.basename(a["path"]) and " " in t and a["relationships"]["exact_duplicates"]:
                    anomalies.append(f"`{r['path']}` alt text `{t}` differs from link target `{os.path.basename(a['path'])}` (space vs underscore form)")
    w(_bullets(sorted(set(anomalies))))
    w("")

    # 8. flagged rights (top questions)
    w("## 8. Open rights and provenance questions")
    w("")
    w("See `catalog/README.md` (\"Rights and provenance\") for how these fields are populated. The blocking questions are:")
    w("")
    for q in manifest["catalog"].get("open_questions", []):
        w(f"1. {q}")
    w("")
    return "\n".join(L) + "\n"


def cmd_report(args) -> int:
    manifest = load_json(Path(args.manifest))
    text = render_report(manifest)
    if args.check:
        ok = REVIEW.exists() and REVIEW.read_text(encoding="utf-8") == text
        print("report: up to date" if ok else "report: STALE")
        return 0 if ok else 1
    REVIEW.write_text(text, encoding="utf-8")
    print(f"report: wrote {REVIEW.relative_to(ROOT)} ({len(text.splitlines())} lines)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(MANIFEST), help="manifest path (default: catalog/asset-manifest.json)")
    ap.add_argument("--schema", default=str(SCHEMA), help="schema path (default: catalog/asset-manifest.schema.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sync", help="refresh derived fields")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_sync)
    p = sub.add_parser("validate", help="validate manifest")
    p.add_argument("--no-report-check", action="store_true", help="skip REVIEW.md freshness check")
    p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("report", help="regenerate catalog/REVIEW.md")
    p.add_argument("--check", action="store_true", help="exit 1 if REVIEW.md is stale; do not write")
    p.set_defaults(fn=cmd_report)
    p = sub.add_parser("facts", help="print derived technical facts")
    p.add_argument("files", nargs="+")
    p.set_defaults(fn=cmd_facts)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
