#!/usr/bin/env python3
"""Build a screenshot gallery as one self-contained HTML page.

A private repo cannot serve its PNGs to a browser (`gh` cannot upload image
attachments and blob `?raw=true` links are not guaranteed to render), so every
frame is embedded as a data URI. The page loads nothing from outside itself and
the script uses only the standard library.

Usage:
    build_gallery.py <shots-dir> <out.html> --title "<page name>" [--captions captions.json]

`<shots-dir>` is scanned for `*.png` (sorted by file name). `captions.json` maps a
file name (with or without `.png`) to either a caption string or
`{"label": "...", "note": "..."}`. Files without a caption are labelled with
their file name.
"""
import argparse
import base64
import html
import json
import pathlib
import struct

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(data: bytes) -> tuple[int, int]:
    """Width and height from the IHDR chunk, which always comes first."""
    if data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError("not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def load_captions(path: pathlib.Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"{path}: expected a JSON object mapping file name to caption")
    captions = {}
    for key, value in raw.items():
        stem = key[:-4] if key.lower().endswith(".png") else key
        if isinstance(value, str):
            captions[stem] = {"label": value, "note": ""}
        elif isinstance(value, dict):
            captions[stem] = {
                "label": str(value.get("label", stem)),
                "note": str(value.get("note", "")),
            }
        else:
            raise SystemExit(f"{path}: caption for {key!r} must be a string or an object")
    return captions


def figure(shot: pathlib.Path, caption: dict[str, str]) -> str:
    data = shot.read_bytes()
    try:
        width, height = png_size(data)
    except ValueError as err:
        raise SystemExit(f"{shot}: {err}") from err
    uri = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    shape = "portrait" if height > width else "landscape"
    label = html.escape(caption["label"])
    note = html.escape(caption["note"])
    note_html = f'\n      <span class="shot-note">{note}</span>' if note else ""
    return f"""
  <figure class="shot {shape}">
    <button type="button" class="frame" aria-label="放大:{label}">
      <img src="{uri}" alt="{label}" width="{width}" height="{height}" loading="lazy">
    </button>
    <figcaption>
      <span class="shot-label">{label}</span>{note_html}
    </figcaption>
  </figure>"""


STYLE = """
  :root {
    --ground: #e8edf1;
    --ink: #14202b;
    --ink-soft: #56687a;
    --ink-faint: #8395a4;
    --accent: #0f5c7a;
    --bezel: #2a3540;
    --shadow: 0 1px 2px rgba(20, 32, 43, .08), 0 8px 24px rgba(20, 32, 43, .07);
    --sans: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif;
    --mono: ui-monospace, "SFMono-Regular", monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground: #101820;
      --ink: #e7eef4;
      --ink-soft: #a3b4c2;
      --ink-faint: #74889a;
      --accent: #6fb8d8;
      --bezel: #05090d;
      --shadow: 0 1px 2px rgba(0, 0, 0, .5), 0 10px 30px rgba(0, 0, 0, .4);
    }
  }
  :root[data-theme="dark"] {
    --ground: #101820;
    --ink: #e7eef4;
    --ink-soft: #a3b4c2;
    --ink-faint: #74889a;
    --accent: #6fb8d8;
    --bezel: #05090d;
    --shadow: 0 1px 2px rgba(0, 0, 0, .5), 0 10px 30px rgba(0, 0, 0, .4);
  }
  body {
    margin: 0;
    background: var(--ground);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 15px;
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
  }
  .wrap {
    max-width: 1080px;
    margin: 0 auto;
    padding: 40px 16px 80px;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }
  header {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-bottom: 24px;
    border-bottom: 2px solid var(--ink);
  }
  h1 {
    margin: 0;
    font-size: clamp(24px, 5vw, 34px);
    line-height: 1.3;
    text-wrap: balance;
  }
  .meta { margin: 0; font-family: var(--mono); font-size: 12px; color: var(--ink-faint); }
  .strip {
    display: flex;
    flex-wrap: wrap;
    gap: 28px;
    align-items: flex-start;
  }
  .shot {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .shot.portrait { flex: 1 1 236px; max-width: 292px; }
  .shot.landscape { flex: 1 1 100%; }
  .frame {
    display: block;
    width: 100%;
    padding: 7px;
    border: 0;
    background: var(--bezel);
    box-shadow: var(--shadow);
    cursor: zoom-in;
  }
  .portrait .frame { border-radius: 26px; }
  .portrait .frame img { border-radius: 19px; }
  .landscape .frame { border-radius: 10px; }
  .landscape .frame img { border-radius: 5px; }
  .frame img { display: block; width: 100%; height: auto; }
  .frame:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
  figcaption { display: flex; flex-direction: column; gap: 3px; }
  .shot-label { font-size: 14px; font-weight: 500; }
  .shot-note { font-size: 13px; line-height: 1.6; color: var(--ink-soft); }
  /* The UA rule for [hidden] is display:none, which `display:flex` below wins
     against, so the overlay needs its own hidden state. */
  #lightbox[hidden] { display: none; }
  #lightbox {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(8, 14, 20, .88);
    cursor: zoom-out;
  }
  #lightbox img {
    max-width: 100%;
    max-height: 100%;
    border-radius: 10px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, .6);
  }
  @media (max-width: 640px) {
    .strip { gap: 22px; }
    .shot.portrait { flex: 1 1 100%; max-width: 340px; }
  }
"""

SCRIPT = """
  const box = document.createElement("div");
  box.id = "lightbox";
  box.hidden = true;
  const full = document.createElement("img");
  full.alt = "";
  box.append(full);
  document.body.append(box);

  function close() {
    box.hidden = true;
    full.removeAttribute("src");
  }

  for (const button of document.querySelectorAll(".frame")) {
    button.addEventListener("click", () => {
      full.src = button.querySelector("img").src;
      box.hidden = false;
    });
  }
  box.addEventListener("click", close);
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
"""


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Embed every PNG in a folder into one self-contained HTML gallery page."
    )
    ap.add_argument("shots_dir", type=pathlib.Path, help="folder holding the *.png screenshots")
    ap.add_argument("out", type=pathlib.Path, help="HTML file to write")
    ap.add_argument("--title", required=True, help="page title")
    ap.add_argument(
        "--captions",
        type=pathlib.Path,
        default=None,
        help='JSON object: {"<file name>": "caption"} or {"<file name>": {"label": "...", "note": "..."}}',
    )
    args = ap.parse_args()

    if not args.shots_dir.is_dir():
        raise SystemExit(f"not a folder: {args.shots_dir}")
    shots = sorted(args.shots_dir.glob("*.png"))
    if not shots:
        raise SystemExit(f"no *.png in {args.shots_dir}")

    captions = load_captions(args.captions)
    known = {shot.stem for shot in shots}
    unused = sorted(set(captions) - known)
    if unused:
        print(f"warning: captions with no matching PNG: {', '.join(unused)}")

    figures = "".join(
        figure(shot, captions.get(shot.stem, {"label": shot.stem, "note": ""}))
        for shot in shots
    )
    title = html.escape(args.title)
    page = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{title}</h1>
    <p class="meta">共 {len(shots)} 張,點圖可放大</p>
  </header>
  <div class="strip">{figures}
  </div>
</div>
<script>{SCRIPT}</script>
</body>
</html>
"""
    args.out.write_text(page, encoding="utf-8")
    print(f"{args.out}  {args.out.stat().st_size / 1_000_000:.2f} MB  ({len(shots)} image(s))")


if __name__ == "__main__":
    main()
