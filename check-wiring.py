#!/usr/bin/env python3
"""Verify every rendition page is wired into the gallery.

Run this after adding a model:

    python3 check-wiring.py

Exits 0 when everything is wired, 1 with a list of problems otherwise.
No dependencies, no network, reads only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
INDEX = ROOT / "index.html"
SKIP = {"index.html"}

problems = []
notes = []


def fail(msg):
    problems.append(msg)


# ---------------------------------------------------------------- gallery
index_html = INDEX.read_text()
entries = re.findall(
    r'\{\s*file:\s*"([^"]+)"\s*,\s*model:\s*"([^"]+)"\s*\}', index_html
)
if not entries:
    fail("index.html: could not find the `tests` array")
    print("\n".join(problems))
    sys.exit(1)

listed_files = [f for f, _ in entries]
listed_models = [m for _, m in entries]

# every rendition file on disk must appear in the gallery, and vice versa
on_disk = sorted(p.name for p in ROOT.glob("*.html") if p.name not in SKIP)
for name in on_disk:
    if name not in listed_files:
        fail(f"index.html: {name} exists on disk but is missing from `tests`")
for name in listed_files:
    if name not in on_disk:
        fail(f"index.html: `tests` references {name}, which is not on disk")

# the gallery must be alphabetical by model name
if listed_models != sorted(listed_models, key=str.lower):
    fail(
        "index.html: `tests` is not alphabetical by model name.\n"
        "         expected: " + ", ".join(sorted(listed_models, key=str.lower))
    )

# the array stores filenames but sorts by model name -- this is the canonical order
expected_pages = [f for f, _ in sorted(entries, key=lambda e: e[1].lower())]

# --------------------------------------------------------- rendition pages
for name in on_disk:
    text = (ROOT / name).read_text()
    where = f"{name}:"

    if 'class="pob-nav"' not in text:
        fail(f"{where} missing the shared `.pob-nav` block "
             f"(copy it from another rendition page)")
        continue

    for el_id in ("prevBtn", "nextBtn"):
        if f'id="{el_id}"' not in text:
            fail(f"{where} nav block has no #{el_id}")

    # a hand-rolled nav with hardcoded hrefs silently drops the page from the rotation
    for stray in re.findall(r'<nav class="(?!pob-nav)([^"]+)"', text):
        fail(f"{where} has a second, non-shared <nav class=\"{stray}\"> — "
             f"remove it so prev/next stays in sync")

    match = re.search(r"var pages = \[(.*?)\];", text, re.S)
    if not match:
        fail(f"{where} nav block has no `var pages` array")
        continue

    pages = re.findall(r'"([^"]+)"', match.group(1))
    if pages != expected_pages:
        missing = [p for p in expected_pages if p not in pages]
        extra = [p for p in pages if p not in expected_pages]
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unknown {', '.join(extra)}")
        if not detail:
            detail.append("wrong order")
        fail(f"{where} `pages` array is out of sync ({'; '.join(detail)})")

    if name not in pages:
        fail(f"{where} does not list itself in `pages`, so prev/next starts from the wrong index")

    # `{{ }}` in CSS is a parse error; the rule silently never applies
    style = "".join(re.findall(r"<style>(.*?)</style>", text, re.S))
    if "{{" in style:
        fail(f"{where} has `{{{{ }}}}` braces in a <style> block — invalid CSS, the rule will not apply")

    # the scene must not render underneath the fixed bar
    if "--pob-nav-h" not in text:
        fail(f"{where} never references --pob-nav-h, so the scene may run under the nav bar")
    elif re.search(r"(?<!- )\b100(?:s|d)?vh\b(?!\s*-)", text) and "position: relative" not in text:
        notes.append(f"{where} sizes to the viewport but body is not `position: relative`; "
                     f"absolutely-positioned children may sit under the bar")

# -------------------------------------------------------------------- out
print(f"{len(on_disk)} rendition pages, {len(entries)} gallery entries")

for note in notes:
    print(f"  note: {note}")

if problems:
    print(f"\n{len(problems)} problem(s):\n")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)

print("all wired correctly")
