# back-matter-builder

Assemble print-ready **book back matter** from a single profile file — for
Kindle Direct Publishing (KDP) paperbacks. One command emits sized, safely
margined HTML (with `@page` geometry set per trim) and clean Markdown, plus a
lint that catches **dangling links** before they reach print.

From [Asdale Dynamics, LLC](https://github.com/dylanasdale) — beginner-friendly
AI education, author tools, and local-first utilities that explain AI "like a
friend would": plain English, step by step, never condescending.

Pairs well with **kdp-interior-templates** (that project owns page geometry
templates; this one owns the *words and pages* of the back matter).

## What it builds

From one JSON or TOML profile it assembles, in print order:

1. **Endnotes** (optional; placed first so notes sit near the body, or last — you choose)
2. **Copyright page** — title, author, notice, publisher, edition, ISBN, boilerplate, extras
3. **Also-by page** — other titles by the author
4. **Series block** — series name, blurb, book list ("← this book" marker), optional link
5. **Review-ask paragraph**
6. **Newsletter link card** — blurb + https link
7. **About the Author**
8. Clean **output lint**: every link in the render is checked (empty `href`,
   bare fragments, TODO/TBD placeholders, example.com, loopback URLs, or
   reference-style links with no definition) and the lint exits non-zero so
   build pipelines stop.

Sizes are real: the emitter asks for your trim and page count, and applies KDP
no-bleed outside/gutter margin rules with the text block math per common KDP
trims (`5x8` through `8.25x11`).

The **rewrite pass** is optional and local-first: with `--rewrite`, each
free-text section (review ask, newsletter blurb, about, endnotes) is rewritten
by any OpenAI-compatible chat endpoint. The default endpoint is **Ollama** at
`http://localhost:11434/v1`; configuration stores a `base_url` only — **never
an API key**. If the endpoint is unreachable, the original text is kept and the
build still succeeds.

## Install

```bash
pip install -e .          # needs Python 3.10+
pip install -e ".[dev]"   # + pytest for the test suite
```

## Quick start

```bash
backmatter init --path my-profile.json   # writes a starter profile to edit
backmatter trims                         # list common KDP trims and their notes
backmatter build --profile my-profile.json \
                 --markdown out.md \
                 --html out.html \
                 --trim 6x9
backmatter lint out.md out.html --profile my-profile.json
```

Add `--rewrite --model llama3.2` to the `build` command to polish prose via
your local model server (Ollama by default; any `--endpoint http://host/v1`
works). The `--check-links` flag makes `build` itself fail on dangling links.

## Profile essentials

```json
{
  "title": "The Massive AI Manual",
  "author": "Dylan Asdale",
  "year": 2026,
  "publisher": "Asdale Dynamics, LLC",
  "trim": "6x9",
  "page_count": 200,
  "also_by": { "books": ["The Massive AI Manual: Quick Start"] },
  "series": {
    "name": "Friend-Explained AI",
    "this_book": "Book 1",
    "books": ["Book 1", "Book 2"],
    "blurb": "Plain-English AI, step by step.",
    "url": "https://dylanasdale.github.io"
  },
  "review_ask": { "text": "Reviews help other beginners find this book." },
  "newsletter": { "url": "https://example.org/newsletter", "blurb": "Monthly, free." },
  "about": { "text": "Dylan Asdale is an RN turned AI author..." },
  "endnotes_placement": "first"
}
```

`endnotes` in the profile is `{ "heading": "Notes", "text": "1. ..." }` with
`endnotes_placement` of `first`, `last`, or `omit`.

## Tests

```bash
pytest
```

Fixtures live in `tests/fixtures/` (a full profile in JSON and TOML, plus a
known-dangling sample). Tests cover profile parsing/validation, trim geometry
against KDP's margin bands, section ordering, HTML/Markdown rendering, the
dangling-link lint, the CLI (build/lint/trims/init), and the rewrite pass
against a stubbed OpenAI-compatible HTTP server.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.
