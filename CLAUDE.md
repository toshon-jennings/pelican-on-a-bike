# Pelicans On Bikes

A static gallery of AI models attempting one prompt: animate a pelican riding a bicycle.
Plain HTML/CSS/SVG, no build step, no dependencies — open `index.html` directly.

- `index.html` — the gallery. Owns the hero animation and the `tests` array.
- `*-pelican-*.html` — one standalone rendition per model. Each is self-contained
  apart from a shared bottom nav block appended at the end of `<body>`.
- `check-wiring.py` — verifies every rendition is wired in. Read-only.

---

# ⚠️ Adding a model: you are not done when the page renders

**A new rendition page is not finished until it is wired into the gallery.**
Dropping the `.html` file in the repo is step 1 of 4. A page that renders
beautifully but is missing from the other pages' `pages` arrays is unreachable —
visitors can never navigate to it, and nobody notices until someone audits it.

This has already gone wrong twice: one page shipped with its own hand-rolled
`<nav>` and hardcoded prev/next hrefs, so it never entered the rotation; another
sat at 14 entries while a 15th page existed.

## The four steps

1. **Add the file.** `<model>-pelican-*.html` in the repo root.
2. **Append the shared nav block.** Copy the `<style>` + `<nav class="pob-nav">` +
   `<script>` from the end of any existing rendition page, changing only the model
   name in the `.pob-nav-home` link and its `aria-label`.
   **Do not write your own nav.** A bespoke nav with hardcoded `href`s cannot stay
   in sync and silently drops the page from every other page's rotation.
3. **Register it in `index.html`** — add `{ file, model }` to `tests`, in
   alphabetical position.
4. **Add it to the `pages` array in _every_ rendition page**, including the new
   one, in the same alphabetical position. The array is byte-identical in all
   pages, so one search-and-replace across `*-pelican-*.html` does it.

## Then verify

```bash
python3 check-wiring.py
```

It must print `all wired correctly` and exit 0. Do not report the task complete
until it does. The checker catches: a page missing from the gallery, a page on
disk that nothing links to, a non-alphabetical listing, a missing or bespoke nav,
a stale `pages` array, a page that omits itself, `{{ }}` braces in CSS, and a
scene that will render under the nav bar.

## Ordering

**Every listing is alphabetical by model _display name_, case-insensitive.**
Insert in position; never append to the end.

Watch the trap: the lists sort by **model name** but the `pages` array stores
**filenames**, and the two do not sort alike — "DeepSeek v4 Flash" is
`pelican-bicycle-deepseekv4flash.html`, which sits between "Composer 2.5 Fast"
and "Gemini 3.6 Flash". Sorting the array as raw filenames will scramble it.

---

## The nav bar

`.pob-nav` is fixed at the bottom, `--pob-nav-h` (64px) tall. The demo scene must
sit **on top of** it, never underneath:

- Pages that size themselves to the viewport use
  `height: calc(100vh - var(--pob-nav-h))` (or `100svh`) **and** set
  `body { position: relative }`. Both are required — without `position: relative`,
  `position: absolute; bottom: 0` children resolve against the viewport rather
  than the shortened body, and the scene slides straight back under the bar.
- Pages that flow normally get a sized, scrollable body instead.

Keep the nav's CSS in a real stylesheet, not inline. An earlier version wrote the
hover rule as `{{ ... }}`, which is a CSS parse error, so the rule never applied.
The same `{{ }}` inside the nav's JavaScript was harmless — in JS it is just a
nested block — which is why the bug hid for so long.

## Hero animation (`index.html`)

The rider is drawn in **one coordinate system with no transform attributes** — the
pelican, bicycle, wheels, limbs, cap brim, beak and scarf are all authored facing
`+x`, and the road and speed lines animate leftward to match. Do not fix a
direction problem by mirroring a sub-group (`scale(-1 1)`); that is what broke it
before. Re-draw the affected parts instead.

Key geometry, if you re-rig it: rear hub `196,402`, bottom bracket `346,402`,
front hub `556,402`. The `.wheel` and `.crank` CSS spins use
`transform-box: fill-box`, so each group's bounding box must stay centred on its
own pivot; `.front-leg`/`.back-leg` pivot on the hip via `transform-box: view-box`.
