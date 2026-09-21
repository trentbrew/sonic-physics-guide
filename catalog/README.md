# Asset Catalog

A stack-neutral semantic catalog of every regular file under [`images/`](../images/). It records what each asset visibly contains, what the documentation says it demonstrates, whether it is suitable for runtime use, what is known about its origin and rights, and how much of its numeric or spatial metadata has been verified.

It assumes no engine, language, renderer or framework. Concepts are described in portable terms: fixed ticks, subpixels, sensors, height masks, frames, pivots.

> Originating proposal: Trellis `TRL-377`. Using Trellis is not required; everything durable lives in this repository.

| File | Purpose |
| --- | --- |
| [`asset-manifest.json`](asset-manifest.json) | The machine-readable manifest: exactly one entry per file under `images/`. |
| [`asset-manifest.schema.json`](asset-manifest.schema.json) | Versioned JSON Schema (draft 2020-12, `x-schema-version` 1.0.0). |
| [`REVIEW.md`](REVIEW.md) | Generated review report: totals, duplicates, orphans, provenance gaps, low-confidence entries, atlas work, unresolved references. |
| [`../scripts/catalog.py`](../scripts/catalog.py) | Validation, sync and report tool. Python 3 standard library only. |

## Commands

```bash
python3 scripts/catalog.py validate   # 20 checks; exit 0 = pass, 1 = fail
python3 scripts/catalog.py sync       # refresh DERIVED fields (never touches authored text)
python3 scripts/catalog.py report     # regenerate catalog/REVIEW.md
python3 scripts/catalog.py facts images/Foo.png   # print derived technical facts for a file
```

The tool never writes to `images/`.

## What `validate` proves

1. The schema declares draft 2020-12, has a semver version equal to the manifest's `schema_version`, and contains no implementation-stack terms.
2. The manifest conforms to the schema (the tool ships its own small validator and refuses schema keywords it does not implement).
3. Every file under `images/` has exactly one entry, every path exists with exact letter case, and ids and paths are unique.
4. Every recorded SHA-256 matches, and every `media` block equals a fresh re-parse of the file headers.
5. Files whose content type disagrees with their extension are flagged.
6. `related_docs` equals a fresh scan of `README.md` and `docs/**/*.md`.
7. Exact-duplicate groups are internally consistent; relationship targets exist; symmetric relations are reciprocal.
8. Every documentation image/asset reference resolves **with exact letter case** (so it also resolves on case-sensitive filesystems).
9. Every `cited_source_url` appears verbatim in repository Markdown.
10. No placeholder, empty or untrimmed text; semantic rules hold (see below).
11. Verified atlas frame regions are reproduced by re-measuring the pixels.
12. `images/` is identical to git `HEAD` (skipped with a note when git is unavailable).
13. `REVIEW.md` is up to date.

The semantic rules include: a documentation diagram or capture can never be `candidate-runtime-art` or `source-data`; a map composite can never be `source-data`; unknown or unclear rights must carry the `rights-unverified` flag; a license may only be recorded with `rights_status: explicit-license`; animated assets need a `sequence`, and every sequence transition must cite a frame that was actually inspected.

## Evidence classes are kept separate

| Question | Where it lives | Rule |
| --- | --- | --- |
| What is visibly in the file? | `summary`, `depicts`, `demonstrates[basis=observed]` | Literal; no game behavior. |
| What does the documentation say it shows? | `demonstrates[basis=documentation]`, `related_docs` | Quoted from repository text, not verified against the image. |
| What is merely a reasoned reading? | `demonstrates[basis=inferred]` | Used sparingly and always flagged by reduced confidence. |
| Is it suitable for runtime use? | `runtime_role`, `runtime_role_rationale` | Independent of how "game-like" the image looks. |
| Are redistribution rights known? | `provenance.rights_status`, `license`, `license_evidence` | Never inferred; unknown stays unknown. |
| Is numeric or spatial metadata verified? | `verification.numeric_spatial_metadata`, `atlas.*.status` | Only measured, reproducible values are marked verified. |

## Taxonomy (`kind`)

| Kind | Meaning |
| --- | --- |
| `sprite-atlas` | Sheet of sprites or poses intended to be cut into frames. |
| `mechanic-demonstration` | Animated capture illustrating a mechanic or bug over time. |
| `mechanic-diagram` | Static diagram of a rule (angles, subpixels, radius). |
| `collision-diagram` | Diagram or annotated screenshot of collision geometry, sensors, ranges or solidity. |
| `terrain-height-mask-reference` | Illustration of height masks or tile profiles. |
| `map-composite` | Composite of level art illustrating map structure. Never treated as level data. |
| `object-hitbox-reference` | Annotated capture of an object's hitbox, solidity or trigger area (still or animated). |
| `control-ui-icon` | Small inline glyph for a controller input. |
| `diagnostic-overlay` | Emulator-side diagnostic script. |
| `documentation-decoration` | Wiki page furniture unrelated to game behavior. |
| `other` | Anything that fits none of the above (currently unused). |

### `runtime_role`

`reference-only` (understand a mechanic, do not load it), `candidate-runtime-art` (could become in-game art after rights and metadata review), `source-data` (could be parsed as data; currently unused, and never allowed for diagrams or map composites), `tooling` (helps observe or validate behavior), `unknown`.

## Confidence model

Every entry has `confidence.level`, a `reason`, `needs_review`, and `review_flags`.

| Level | Meaning |
| --- | --- |
| `high` | Everything material was directly visible or stated by the text, and nothing significant was left uninspected. |
| `medium` | The description is sound, but part of it rests on sampling, small text, an unlabelled legend, or a documentation claim that could not be checked. |
| `low` | The key behavior or meaning could not be established from what was inspected. `needs_review` is then mandatory. |

Review flags: `provenance-unverified`, `rights-unverified`, `atlas-frame-boundaries`, `atlas-pivots`, `atlas-pose-names`, `description-uncertain`, `sequence-interpretation-partial`, `numeric-values-unverified`, `format-extension-mismatch`, `documentation-claim-unverified`, `duplicate-filename-variant`, `doc-alt-text-mismatch`.

`verification.visual_inspection` states how the file was inspected: `full`, `all-frames` (short animations), `sampled-frames` (with the exact 1-based frame numbers in `inspected_frames`), or `source-text-review`. Events between sampled frames were **not** observed.

## Field ownership

*Derived* fields are computed by `sync` and re-checked by `validate`; do not edit them by hand: `sha256`, `media.*`, `related_docs`, `provenance.source_pages`, `relationships.exact_duplicate_of`, `relationships.exact_duplicates`. Everything else is authored and is never rewritten by the tool.

Media facts are read from file headers, and the format is decided by **content signature, never by extension**. `media.alpha.mode` states how transparency is encoded; for GIFs a declared transparent index (common for delta frames) does not prove the composited animation has see-through pixels, so pixel-level fields are `null` there. Frame delays are the encoded GIF values.

## How a future implementation should consume this

1. **Load `asset-manifest.json` and check `schema_version`.** Reject a major version you do not understand.
2. **Verify integrity.** Compare each file's SHA-256 with the manifest before trusting anything derived from it.
3. **Decode by signature.** Seven files have a misleading extension: six GIFs named `.png`/`.PNG` and one JPEG named `.png`. Never dispatch on extension. `media.extension_matches_format` says which.
4. **Filter by `runtime_role`.** Only `candidate-runtime-art` is a candidate for in-game use, and only after a rights decision: check `provenance.rights_status`. `restricted-or-unclear` and `unknown` are not permissions.
5. **Take numbers from the documentation, not the pictures.** Diagrams and captures illustrate rules; hitbox radii, angle ranges and timings belong in your own data, sourced from the guide's text. Numbers transcribed from images carry `numeric-values-unverified`.
6. **Treat map composites as illustrations.** They are not level layouts or tile data.
7. **Atlases.** `frame_regions.regions` are tight pixel bounds `[x, y, width, height]` (origin top-left, y down), measured and reproducible, but they are not authoring cell rectangles and not stable anchors. Pose names, animation order, durations, mirroring rules and pivots are **not established**: do not derive collision geometry from sprite bounds, and do not assume the per-row descriptions in `docs/23-implementation-guide.md` (see `REVIEW.md`).
8. **Animations.** `sequence` summarizes the starting state, transitions (1-based frame numbers), ending behavior, mechanic illustrated and notable changes. One GIF frame is not one simulation tick.
9. **Duplicates.** Prefer the canonical entry; `relationships.exact_duplicates` lists byte-identical copies. Related but non-identical variants use `relationships.related`.
10. **Ids are stable.** Ids are semantic (`hitbox.motobug`, `diagram.floor-landing-ranges`) and do not change when a file is renamed; paths may.
11. **Implementation notes are portable guidance**, e.g. represent positions as whole pixels plus an 8-bit fractional part, or model sensors as named offsets relative to an object origin.

## Rights and provenance

* `cited_source_url` is set only for a URL that appears verbatim in repository documentation for that specific file. Today that is the two Lua overlay scripts.
* `source_pages` lists the upstream Sonic Retro pages whose converted Markdown references the file. They are pages, not file URLs.
* `acquisition.method` is `scraped-from-wiki` when repository evidence (the scraper and the referencing pages) indicates it, `manually-added` for the two spritesheets added by hand, and `unknown` otherwise. Scraper attribution is an inference from repository evidence, not a per-file record.
* `rights_status` is a cataloguing label, not legal advice. `restricted-or-unclear`: the file depicts or is composed of commercial game imagery and nothing in the repository grants permission. `unknown`: nothing at all is recorded. `explicit-license`: a license and the evidence for it are recorded (currently no entry qualifies).
* `creator` is filled only when the file or the documentation names one (the Lua scripts).

## Known limitations

* Visual inspection was performed by an AI model. Long animations were sampled, not watched end to end.
* Documentation claims are recorded but not adjudicated; where a claim conflicts with observation or with other documentation, the entry says so (for example the spritesheet row list).
* The Sonic Retro file pages were not fetched, so per-file authors and licenses are unknown.
* Angle and size labels read from images are transcriptions, not verified physics values.

## Maintaining the catalog

1. Add or change a file under `images/`. `validate` fails until it has an entry.
2. Run `python3 scripts/catalog.py sync`. A new file gets a clearly marked **UNREVIEWED** stub with low confidence and derived facts filled in.
3. Replace the stub text with reviewed descriptions; keep evidence classes separate and set confidence honestly.
4. Run `python3 scripts/catalog.py report`, then `python3 scripts/catalog.py validate`.
