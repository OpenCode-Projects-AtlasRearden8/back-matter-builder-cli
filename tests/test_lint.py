from __future__ import annotations

from backMatterBuilder import lint

MD_DANGLING = "**Blurb**\n\n[Read more]()\n\n[Join](#)\n\n[TODO](http://link-is-todo.example/)"
MD_CLEAN = "[Great site](https://dylanasdale.github.io)\n\nAlso a plain sentence."
HTML_DANGLING = '<p><a href="https://example.com">x</a><a href="">empty</a></p>'
HTML_CLEAN = '<p><a href="https://dylanasdale.github.io">hub</a></p>'


def test_empty_and_fragment_markdown_links():
    issues = lint.lint_text(MD_DANGLING, "mem.md", "markdown")
    reasons = [i.reason for i in issues]
    assert len(issues) == 3
    assert any("empty URL" in r for r in reasons)
    assert any("bare fragment" in r for r in reasons)
    assert any("placeholder" in r for r in reasons)


def test_markdown_clean_has_no_issues():
    assert lint.lint_text(MD_CLEAN, "ok.md", "markdown") == []


def test_html_empty_href_and_example_com():
    issues = lint.lint_text(HTML_DANGLING, "out.html", "html")
    assert len(issues) == 2


def test_html_clean():
    assert lint.lint_text(HTML_CLEAN, "out.html", "html") == []


def test_loopback_urls_flagged():
    text = "[Fallback](http://127.0.0.1:4000/x)"
    issues = lint.lint_text(text, "a.md", "markdown")
    assert issues and "loopback" in issues[0].reason


def test_undefined_reference_link_flagged():
    text = "See the [guide] for details."
    issues = lint.lint_text(text, "b.md", "markdown")
    assert any("no URL definition" in i.reason for i in issues)


def test_defined_reference_link_is_fine():
    text = "See the [guide] for details.\n\n[guide]: https://dylanasdale.github.io/reference"
    assert lint.lint_text(text, "c.md", "markdown") == []


def test_lint_files_names_kinds(tmp_path):
    p = tmp_path / "out.html"
    p.write_text(HTML_DANGLING)
    issues = lint.lint_files([str(p)])
    assert issues and issues[0].kind == "html"


def test_lint_profile_catches_blurb_without_url():
    from backMatterBuilder.profile import load_profile_from_dict

    p = load_profile_from_dict(
        {
            "title": "T",
            "author": "A",
            "year": 2026,
            "newsletter": {"blurb": "Please subscribe."},
        }
    )
    issues = lint.lint_profile(p)
    assert any("newsletter.url is empty" in i.reason for i in issues)


def test_lint_profile_flags_loopback_newsletter_url():
    from backMatterBuilder.profile import load_profile_from_dict

    p = load_profile_from_dict(
        {
            "title": "T",
            "author": "A",
            "year": 2026,
            "newsletter": {"url": "http://localhost:8787/sub", "blurb": "hey"},
        }
    )
    issues = lint.lint_profile(p)
    assert any("loopback" in i.reason for i in issues)


def test_lint_profile_ok(profile_full):
    assert lint.lint_profile(profile_full) == []
