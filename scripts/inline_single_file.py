#!/usr/bin/env python3
"""Fold a vite build into one Artifact-ready HTML fragment.

An Artifact page cannot load anything from outside itself, so the JS and CSS
that `vite build` emits as separate files have to move into the page. The
Artifact runtime also supplies its own `<!doctype>`, `<html>`, `<head>` and
`<body>`, so this writes the *contents* of the body — a `<title>`, a `<style>`,
the mount point, and one inline module script — and nothing else.

Usage:
    inline_single_file.py <build-dir> <out.html> [--title "..."]

`<build-dir>` is the vite `outDir`; it must hold an `index.html` referencing
its assets with relative paths (build with `base: "./"`).
"""
import argparse
import pathlib
import re


def find_index(build: pathlib.Path) -> pathlib.Path:
    """The built entry. Vite nests it when the input html sits in a subfolder."""
    direct = build / "index.html"
    if direct.is_file():
        return direct
    nested = sorted(build.rglob("index.html"))
    if not nested:
        raise SystemExit(f"no index.html under {build}")
    return nested[0]


def read_asset(base: pathlib.Path, src: str) -> str:
    """`base` is the directory holding index.html — hrefs are relative to it."""
    path = (base / src).resolve()
    if not path.is_file():
        raise SystemExit(f"asset referenced by index.html is missing: {src}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("build_dir", type=pathlib.Path)
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--title", default=None, help="overrides the built <title>")
    args = ap.parse_args()

    index = find_index(args.build_dir.resolve())
    base = index.parent
    html = index.read_text(encoding="utf-8")

    title = args.title
    if title is None:
        found = re.search(r"<title>(.*?)</title>", html, re.S)
        title = found.group(1).strip() if found else "原型"

    styles = [
        read_asset(base, m.group(1))
        for m in re.finditer(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html)
    ]
    scripts = [
        read_asset(base, m.group(1))
        for m in re.finditer(r'<script[^>]+type="module"[^>]+src="([^"]+)"', html)
    ]
    if not scripts:
        raise SystemExit("index.html has no module script — nothing to inline")

    # `</script>` inside the bundle would close the tag we are writing.
    scripts = [s.replace("</script>", "<\\/script>") for s in scripts]

    body = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    mount = body.group(1) if body else '<div id="root"></div>'
    mount = re.sub(r"<script\b.*?</script>", "", mount, flags=re.S).strip()

    parts = [f"<title>{title}</title>"]
    for css in styles:
        parts.append(f"<style>\n{css}\n</style>")
    parts.append(mount)
    for js in scripts:
        parts.append(f'<script type="module">\n{js}\n</script>')

    args.out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    kb = args.out.stat().st_size / 1024
    print(f"{args.out}  {kb:.0f} KB  ({len(styles)} stylesheet(s), {len(scripts)} script(s))")


if __name__ == "__main__":
    main()
