# Library — contract

This directory holds the transitrix.com library of free reference material. The shape
below is enforced by `scripts/check_library.py` in CI (`.github/workflows/library.yml`)
— an item that violates it fails the check rather than reaching a reader.

- **One directory per item:** `library/<slug>/`, served at
  `https://transitrix.com/library/<slug>/`.
- **The source lives at `library/<slug>/<slug>.source.html`.** This is the committed,
  human-authored content — the words are its author's. It is never edited by a
  rendering step; only read.
- **The PDF lives at `library/<slug>/<slug>.pdf`, rendered from the source, never
  hand-authored.** `scripts/render_library_item.py <slug>` renders it via headless
  Chrome on an agent's own host, offline, and asserts the result's page count and
  geometry against the source's own `@page` rule before it is committed. CI never
  renders — see "Checked, not rendered" below. The filename is the slug, so a revision
  replaces the file in place and never mints a second URL.
- **The source's `<title>` leads with the item's own printed name** — read from the
  source's own `<h1>` — with no suffix beyond the site's existing ` | Transitrix`.
- **Kinds of material are not path segments.** A cheat sheet, a template and a worked
  example all sit directly under `library/<slug>/`; grouping belongs on the index page,
  where it can be revised, never in an address that has been printed and handed out.
- **No gate of any kind.** No form, no email field, no sign-up, no interstitial, no
  tracking wall, on the source or on any item page.
- **The typefaces are vendored, not fetched.** A source pulls its fonts from
  `/assets/fonts/`, declared with local `@font-face`; nothing under `library/` may
  depend on a third-party font host or any other network fetch at render time.
- **`SHA256SUMS` carries a pair of entries per item** — `<slug>/<slug>.source.html`
  and `<slug>/<slug>.pdf` — one `<sha256>  <path>` line each (`sha256sum` output
  format), updated in the same commit as the files they describe.

## Checked, not rendered

`scripts/check_library.py` verifies the *committed* pair — it never launches a
browser and never re-renders to check its work. Concretely it checks: the checksum
pair against the committed files, the PDF's page count and its `MediaBox` against
the source's own `@page` rule, the no-gate patterns against the source, and the
source's `<title>` against its own `<h1>`.

**A source edited without re-rendering is caught as an ordinary checksum
mismatch**, the same way a tampered PDF already was: `SHA256SUMS` is only ever
updated by the render step, so an edit that skips it leaves the source's committed
bytes disagreeing with the hash recorded for it.

**Do not add a check that re-renders and diffs the two PDFs to verify a render is
current.** It cannot work: a browser embeds a creation date in the PDF it writes,
and rendered output shifts across Chrome milestones, so two renders of the same
source are not byte-identical even seconds apart — the diff would fail on nothing,
every time, and teach everyone to ignore it. This has already been tried once; it
is written here so it is not tried again.
