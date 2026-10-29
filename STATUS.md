# STATUS.md

## What was built

`back-matter-builder` — a local-first, offline-by-default Python CLI that
assembles print-ready book back matter from a single profile file (JSON or
TOML), sized for common KDP paperbacks.

**Package:** `backMatterBuilder` (script name: `backmatter`)

- `trims.py` — 11 common KDP trim sizes (5x8 through 8.25x11) and KDP
  no-bleed outside/gutter margin bands by page count (24–820 pp), plus
  text-block math.
- `profile.py` — profile loading (JSON/TOML), dataclass model, validation
  (required fields, unknown keys, URL shape, rewrite config, endnotes
  placement of `first`/`last`/`omit`).
- `sections.py` — builds pages in print order: endnotes (first), copyright
  (title, notice, publisher, edition, ISBN, boilerplate, extras), also-by,
  series block with "← this book" marker + optional link, review-ask,
  newsletter card, about-the-author, endnotes (last).
- `render.py` — HTML emitters with `@page` size per trim, KDP-derived
  margins (pt, from the trim + page count), forced page breaks per page;
  and clean shared-friendly Markdown with headings/links.
- `lint.py` — dangling-link lint for rendered output and profiles: empty
  href/URL, bare fragments, TODO/TBD/CHANGE-ME/placeholder hosts, example.*
  URLs, loopback URLs (never reader-facing), undefined reference-style
  markdown links, and https-recommendations for profile links.
- `rewrite.py` — optional rewrite pass against any OpenAI-compatible chat
  endpoint. Default base_url is Ollama `http://localhost:11434/v1`.
  Configuration stores **only a base_url — never an API key**. Endpoint
  failures warn and keep original text (build never fails for it).
- `cli.py` — subcommands `build`, `lint`, `trims`, `init`; flags
  `--trim`, `--rewrite`, `--endpoint`, `--model`, `--check-links`,
  `--allow-dangling`.

Includes `LICENSE` (MIT, "Copyright (c) 2026 Asdale Dynamics, LLC") and a
README crediting Asdale Dynamics, LLC. Complements the sibling project
`kdp-interior-templates` (which owns page-geometry templates; this owns the
words and pages of the back matter).

## How to run it

```bash
pip install -e ".[dev]"      # Python 3.10+
backmatter init --path my-profile.json
backmatter trims
backmatter build --profile my-profile.json --markdown out.md --html out.html --trim 6x9
backmatter lint out.md out.html --profile my-profile.json
backmatter build --profile my-profile.json --markdown out.md --rewrite   # optional local LLM pass
```

Note: `lint` takes *rendered* files as positional arguments; use `--profile`
to lint the profile itself. Exit code 1 = dangling links found.

## Verification (2026-10-29)

- `pytest`: **64/64 passed** (profile parsing/validation incl. TOML, trim
  geometry against KDP margin bands, section print order & omissions,
  HTML/Markdown rendering, dangling-link lint, CLI end-to-end on temp files,
  rewrite pass against a stubbed OpenAI-compatible HTTP server, and graceful
  degradation when no model server is listening).
- `pip install -e .` succeeded; `backmatter --version` → `0.1.0`.
- End-to-end run on `example-profile.json`: build produced 7 print pages
  (endnotes, copyright, also-by, series, review-ask, newsletter, about) at
  trim 6x9 with correct `@page: 6in 9in` and KDP margins for ~200 pages;
  `--check-links` clean; lint clean.
- Dangling-link demo: a profile with a placeholder newsletter URL fails
  `lint` (exit 1) with a precise message; `build --check-links` refuses to
  write unless `--allow-dangling`.
- `--rewrite` without a running Ollama: warns per section and keeps original
  text, exit code 0.

## Known gaps

- Margins use KDP **no-bleed minimums**; no bleed option and no `mirror`
  margins spread per recto/verso page in CSS (single shared margin is
  written; production typesetting applies mirrored gutters in the PDF step).
- Trim sizes are paperback; KDP hardcover trims are not included.
- Markdown lint is a focused dangling-link checker, not a full Markdown
  validator.
- The rewrite pass never sends any secret (no key support by design). If an
  endpoint needs auth, proxy it locally; that proxy responsibility is
  out of scope.
- No `py.typed`/type-stub packaging; type hints are present in code.
