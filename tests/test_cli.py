from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from backMatterBuilder.cli import build_parser, cmd_build, main

from tests.test_rewrite import FakeOpenAIHandler


@pytest.fixture
def fake_endpoint():
    server = HTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1"
    server.shutdown()


def test_build_writes_html_and_markdown(tmp_path, profile_json_file, capsys):
    out_html = tmp_path / "out.html"
    out_md = tmp_path / "out.md"
    rc = main(
        [
            "build",
            "--profile",
            str(profile_json_file),
            "--html",
            str(out_html),
            "--markdown",
            str(out_md),
        ]
    )
    assert rc == 0
    html = out_html.read_text()
    assert "<html" in html and "@page" in html
    assert "Copyright (c) 2026 Dylan Asdale" in html
    md = out_md.read_text()
    assert "## Notes" in md and "## About the Author" in md
    captured = capsys.readouterr()
    assert "wrote" in captured.out


def test_build_minimal_profile(tmp_path, fixture_dir):
    out_md = tmp_path / "tiny.md"
    rc = main(
        "build --profile {f} --markdown {o}".format(f=fixture_dir / "profile_minimal.json", o=out_md).split()
    )
    assert rc == 0
    assert "Copyright (c) 2026 Test Author" in out_md.read_text()


def test_build_check_links_fails_on_bad_profile(tmp_path, fixture_dir, capsys):
    rc = main(
        [
            "build",
            "--profile",
            str(fixture_dir / "profile_dangling.json"),
            "--markdown",
            str(tmp_path / "bad.md"),
            "--check-links",
        ]
    )
    assert rc == 1
    assert not (tmp_path / "bad.md").exists()
    assert "dangling links found" in capsys.readouterr().out


def test_build_check_links_allow_dangling(tmp_path, fixture_dir):
    out_md = tmp_path / "bad.md"
    rc = main(
        [
            "build",
            "--profile",
            str(fixture_dir / "profile_dangling.json"),
            "--markdown",
            str(out_md),
            "--check-links",
            "--allow-dangling",
        ]
    )
    assert rc == 0
    assert out_md.exists()


def test_build_check_links_clean_profile_passes(tmp_path, profile_json_file):
    rc = main(["build", "--profile", str(profile_json_file), "--markdown", str(tmp_path / "out.md"), "--check-links"])
    assert rc == 0


def test_trim_override(tmp_path, profile_json_file):
    out = tmp_path / "out.html"
    rc = main(
        [
            "build",
            "--profile",
            str(profile_json_file),
            "--html",
            str(out),
            "--trim",
            "8x10",
        ]
    )
    assert rc == 0
    assert "size: 8in 10in;" in out.read_text()


def test_lint_command_reports(tmp_path, fixture_dir, capsys):
    html = tmp_path / "x.html"
    html.write_text('<a href="">dangling</a>')
    rc = main(["lint", str(html)])
    assert rc == 1
    assert "1 dangling link(s)" in capsys.readouterr().out


def test_lint_command_clean_file(tmp_path, profile_json_file):
    out_md = tmp_path / "out.md"
    main(["build", "--profile", str(profile_json_file), "--markdown", str(out_md)])
    assert main(["lint", str(out_md)]) == 0


def test_lint_profile_flag(tmp_path, fixture_dir, capsys):
    rc = main(["lint", "--profile", str(fixture_dir / "profile_dangling.json")])
    assert rc == 1
    assert "newsletter" in capsys.readouterr().out


def test_trims_command(capsys):
    assert main(["trims"]) == 0
    out = capsys.readouterr().out
    assert "6x9" in out and "8.25x11" in out


def test_init_command(tmp_path, capsys):
    target = tmp_path / "new-profile.json"
    assert main(["init", "--path", str(target)]) == 0
    assert target.exists()
    assert "starter profile" in capsys.readouterr().out


def test_init_refuses_overwrite(tmp_path):
    target = tmp_path / "new-profile.json"
    target.write_text("x")
    assert main(["init", "--path", str(target)]) == 2


def test_rewrite_via_cli_replaces_text(
    tmp_path, fixture_dir, fake_endpoint, capsys
):
    import json

    profile = json.loads((fixture_dir / "profile_full.json").read_text())
    profile["rewrite"] = {"base_url": fake_endpoint, "model": "test-model", "sections": ["review_ask"]}
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile))
    out_md = tmp_path / "out.md"
    rc = main(["build", "--profile", str(path), "--markdown", str(out_md), "--rewrite"])
    assert rc == 0, capsys.readouterr().out
    md = out_md.read_text()
    assert "REWRITTEN::test-model::" in md


def test_bad_profile_returns_error_code(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{"author": "no-title"}')
    rc = main(["build", "--profile", str(bad), "--markdown", str(tmp_path / "x.md")])
    assert rc == 2


def test_build_needs_output_targets_or_noop(tmp_path, profile_json_file):
    rc = main(["build", "--profile", str(profile_json_file)])
    assert rc == 0


def test_parser_accepts_version():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
