# Library

This directory holds the transitrix.com library of free reference material. The
shape below is enforced by `scripts/check_library.py` in CI
(`.github/workflows/library.yml`) — an item that violates it fails the check
rather than reaching a reader.

- **One directory per item:** `library/<slug>/`, served at
  `https://transitrix.com/library/<slug>/`.
- **The PDF lives at `library/<slug>/<slug>.pdf`.** This is the file a reader
  downloads. A revision replaces the file in place and never mints a second URL.
- **Kinds of material are not path segments.** A cheat sheet, a template and a
  worked example all sit directly under `library/<slug>/`; grouping belongs on
  the index page, where it can be revised, never in an address that has been
  printed and handed out.
- **No gate of any kind.** No form, no email field, no sign-up, no interstitial,
  no tracking wall, on the sheet or on any item page.
- **`SHA256SUMS` carries one entry per item** — `<slug>/<slug>.pdf` — one
  `<sha256>  <path>` line (`sha256sum` output format), updated in the same
  commit as the file it describes.

## Checked against the published PDF

`scripts/check_library.py` verifies the *committed* PDF — it never launches a
browser and never re-renders. Concretely it checks: the checksum against the
committed file, the PDF's page count and its `MediaBox` against the sheet size
(297 × 167 mm), and the no-gate patterns against the PDF's own extracted text.

**Do not add a check that re-renders and diffs the two PDFs.** It cannot work: a
browser embeds a creation date in the PDF it writes, and rendered output shifts
across Chrome milestones, so two renders of the same input are not
byte-identical even seconds apart — the diff would fail on nothing, every time,
and teach everyone to ignore it. This has already been tried once; it is written
here so it is not tried again.

This check cannot tell whether a PDF is current with a file that is not in this
repository. A check that appears to cover that and does not is worse than its
absence.

## Page title rule — the search query, then the promise

The page title contains the search query, and then earns the click. It carries, as a contiguous string, the words a reader actually types — so the match is visible in the result itself — and continues with what the reader gets: what is covered, how completely, which version, at what cost of entry. The sheet's printed name stays recognisably inside it, so a link handed out on paper and the page still agree. The title leads with the subject, never with the brand — the brand is the site suffix ` | Transitrix` and nothing more — and it does not sell: no superlatives, no campaign wording, no promise the sheet does not keep. Roughly 60 characters before the site suffix, because what is cut off cannot be read.

**Form:** `<subject> — <what is covered>, <completeness>, <cost of entry> | Transitrix`

Example: `ArchiMate 3.2 cheat sheet — 60 elements, free PDF, no sign-up | Transitrix`
