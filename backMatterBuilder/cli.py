"""CLI: assemble, lint, list trims, or scaffold a back-matter profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, lint, render, sections, trims
from .profile import ProfileError, load_profile
from .rewrite import rewrite_section

EXIT_OK = 0
EXIT_DANGLING = 1

SAMPLE_PROFILE = {
    "title": "The Massive AI Manual",
    "author": "Dylan Asdale",
    "year": 2026,
    "publisher": "Asdale Dynamics, LLC",
    "trim": "6x9",
    "page_count": 200,
    "copyright": {
        "extras": ["All AI walkthroughs were run and re-run before publication."],
    },
    "also_by": {"books": []},
    "series": {"name": "", "books": [], "blurb": "", "url": ""},
    "review_ask": {"text": ""},
    "newsletter": {"url": "", "blurb": ""},
    "about": {"text": ""},
    "endnotes_placement": "first",
    "rewrite": {
        "enabled": False,
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.2",
    },
}

ENDNOTES_SECTIONS = {"review_ask", "newsletter", "about", "endnotes"}  # rewrite targets


def _write_if(path: str | None, text: str) -> None:
    if path:
        Path(path).write_text(text, encoding="utf-8")


def cmd_build(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    pages = _build_pages(profile)

    if args.rewrite:
        _apply_rewrite(pages, profile, args)

    html = render.render_html(pages, profile, args.trim)
    md = render.render_markdown(pages, profile)

    if args.check_links:
        issues = lint.lint_text(html, where=args.html or "<html>", kind="html")
        issues += lint.lint_text(md, where=args.markdown or "<markdown>", kind="markdown")
        _report(issues, "pre-write link check")
        if issues and not args.allow_dangling:
            print("build stopped: dangling links found (use --allow-dangling to keep files)")
            return EXIT_DANGLING
    _write_if(args.html, html)
    _write_if(args.markdown, md)
    if args.html:
        print(f"wrote {args.html} ({len(pages)} pages, trim {profile.trim})")
    if args.markdown:
        print(f"wrote {args.markdown}")
    return EXIT_OK


def _build_pages(profile):
    return sections.build_pages(profile)


def _apply_rewrite(pages, profile, args) -> None:
    base = args.endpoint
    model = args.model
    if base:
        profile.rewrite["base_url"] = base.rstrip("/")
    if model:
        profile.rewrite["model"] = model
    if not args.model and not profile.rewrite.get("model"):
        profile.rewrite["model"] = "llama3.2"
    targets = set(profile.rewrite.get("sections") or [])
    for page in pages:
        if page.kind in targets and page.body.strip():
            rewritten = rewrite_section(page.kind, page.body, profile)
            if rewritten != page.body:
                page.body = rewritten


def _report(issues, label: str) -> None:
    if not issues:
        print(f"{label}: clean")
        return
    print(f"{label}: {len(issues)} dangling link(s)")
    for issue in issues:
        print(f"  {issue}")


def cmd_lint(args: argparse.Namespace) -> int:
    issues: list = []
    if args.profile:
        issues += lint.lint_profile(load_profile(args.profile))
    issues += list(lint.lint_files(args.files, kind=args.kind)) if args.files else []
    _report(issues, "lint")
    return EXIT_DANGLING if issues else EXIT_OK


def cmd_trims(_args: argparse.Namespace) -> int:
    print("Common KDP paperback trims (use the key with --trim):")
    for key in sorted(trims.TRIMS):
        t = trims.TRIMS[key]
        print(f"  {key:<11} {trims.format_trim_name(key):<16} {t.note}")
    print(f"  default: {trims.DEFAULT_TRIM}")
    return EXIT_OK


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists():
        print(f"refusing to overwrite {path}")
        return 2
    indent = 4
    path.write_text(
        json.dumps(SAMPLE_PROFILE, indent=indent) + "\n", encoding="utf-8"
    )
    print(
        f"wrote starter profile to {path} - edit it, then run: "
        f"backmatter build --profile {path} --markdown out.md"
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="backmatter",
        description=(
            "Assemble KDP-ready book back matter (copyright, also-by, series, "
            "review ask, newsletter, about, endnotes) from a profile file."
        ),
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="build back matter to HTML and/or Markdown")
    b.add_argument("--profile", required=True, help="profile .json or .toml file")
    b.add_argument("--html", help="output HTML path")
    b.add_argument("--markdown", "--md", dest="markdown", help="output Markdown path")
    b.add_argument("--trim", help="trim key override, e.g. 5.5x8.5")
    b.add_argument(
        "--rewrite",
        action="store_true",
        help="run the optional LLM rewrite pass (endpoint from profile or --endpoint)",
    )
    b.add_argument(
        "--endpoint",
        help="OpenAI-compatible base_url for the rewrite pass (default: profile value, "
        "which defaults to Ollama at http://localhost:11434/v1). Never supply a key here.",
    )
    b.add_argument("--model", help="chat model name for the rewrite pass")
    b.add_argument(
        "--check-links",
        action="store_true",
        help="lint the rendered output and fail the build on dangling links",
    )
    b.add_argument(
        "--allow-dangling",
        action="store_true",
        help="with --check-links, keep writing output even if dangling links were found",
    )
    b.set_defaults(func=cmd_build)

    l = sub.add_parser("lint", help="lint output files and/or a profile for dangling links")
    l.add_argument("files", nargs="*", help="rendered .html or .md files to lint")
    l.add_argument("--profile", help="profile file to validate")
    l.add_argument(
        "--kind",
        choices=["auto", "html", "markdown"],
        default="auto",
        help="force a file kind (default: auto-detect)",
    )
    l.set_defaults(func=cmd_lint)

    t = sub.add_parser("trims", help="list known KDP trim sizes and their margin rules")
    t.set_defaults(func=cmd_trims)

    i = sub.add_parser("init", help="write a starter profile you can edit")
    i.add_argument("--path", default="profile.json", help="where to write (default profile.json)")
    i.set_defaults(func=cmd_init)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ProfileError as exc:
        print(f"profile error: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
