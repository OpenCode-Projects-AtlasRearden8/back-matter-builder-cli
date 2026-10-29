"""Lint for dangling links in rendered back matter.

A link is 'dangling' when it references nothing useful: empty URL, bare
fragment, placeholder text (TODO / TBD / CHANGE ME / example.com), or a
localhost URL that would never resolve for a reader.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .profile import Profile


@dataclass
class LinkIssue:
    where: str  # file or '<profile>'
    line_no: int
    kind: str  # 'html' | 'markdown' | 'profile'
    reason: str

    def __str__(self) -> str:
        return f"{self.where}:{self.line_no}: dangling {self.kind} link - {self.reason}"


_HTML_HREF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_MD_REFERENCE = re.compile(r"\[([^\]]+)\]:\s*(\S+)")


def _check_url(url: str) -> str:
    """Return a reason string if the url is dangling, else ''."""
    u = url.strip()
    if not u:
        return "empty URL"
    if u.startswith("#") and len(u) <= 1:
        return "bare fragment"
    lowered = u.lower()
    bad_hosts = (
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "[::1]",
    )
    m = re.match(r"^https?://([^/:?#]+)", u.lower())
    if m and (m.group(1) in {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"}):
        # an LLM endpoint is a runtime setting, never a reader-facing link;
        # any loopback href is dangling for its audience
        return f"loopback URL ({m.group(1)}) would never resolve for a reader"
    if re.search(r"example\.(com|org|net|io)", lowered):
        return "example.com placeholder URL"
    for token in ("todo", "tbd", "change me", "placeholder", "your-newsletter-link",
                  "yourlink", "your-link"):
        clean = lowered.strip("/ ")
        if token in clean:
            return f"placeholder URL ({token.upper()})"
    return ""


def lint_text(text: str, where: str, kind: str) -> list[LinkIssue]:
    issues: list[LinkIssue] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if kind == "html":
            for url in _HTML_HREF.findall(line):
                url = url.strip()
                reason = ""
                if not url:
                    reason = "empty href"
                else:
                    reason = _check_url(url)
                if reason:
                    issues.append(LinkIssue(where, line_no, kind, reason))
        else:
            for _text_part, url in _MD_LINK.findall(line):
                reason = _check_url(url)
                if reason:
                    issues.append(LinkIssue(where, line_no, kind, reason))
            for _label, url in _MD_REFERENCE.findall(line):
                reason = _check_url(url)
                if reason:
                    issues.append(LinkIssue(where, line_no, kind, reason))
            if _MD_LINK.search(line):
                pass  # well-formed page links were checked above
    # dangling markdown reference-style links: [text] with no matching def
    if kind != "html":
        refs = {label: True for label, _ in _MD_REFERENCE.findall(text)}
        for label in re.findall(r"\[([^\]]+)\](?!\()", text):
            if label.strip() and label.strip() not in refs and not label.startswith("!"):
                issues.append(
                    LinkIssue(
                        where,
                        text.count("\n", 0, text.find(f"[{label}]")) + 1,
                        kind,
                        f"reference-style link '{label}' has no URL definition",
                    )
                )
    return issues


def lint_files(paths: Iterable[str], kind: str = "auto") -> list[LinkIssue]:
    issues: list[LinkIssue] = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        k = kind
        if k == "auto":
            k = "html" if re.search(r"<(html|section|a)\b|href\s*=", text[:4096], re.IGNORECASE) else "markdown"
        issues += lint_text(text, where=path, kind=k)
    return issues


def lint_profile(profile: Profile) -> list[LinkIssue]:
    issues: list[LinkIssue] = []
    for name, url in (
        ("newsletter.url", profile.newsletter.url),
        ("series.url", profile.series.url),
    ):
        if url and (reason := _check_url(url)):
            issues.append(LinkIssue("<profile>", 0, "profile", f"{name}: {reason}"))
        elif url.startswith("http://"):
            issues.append(
                LinkIssue("<profile>", 0, "profile", f"{name} should use https in print")
            )
    if profile.newsletter.blurb and not profile.newsletter.url:
        issues.append(
            LinkIssue(
                "<profile>", 0, "profile", "newsletter blurb set but newsletter.url is empty"
            )
        )
    return issues
