# Reference sheets — contract

This directory holds the transitrix.com reference-sheet library. The shape below is
enforced by `scripts/check_reference_sheets.py` in CI
(`.github/workflows/reference-sheets.yml`) — a sheet that violates it fails the check
rather than reaching a reader.

- **One directory per sheet:** `reference-sheets/<slug>/`, served at
  `https://transitrix.com/reference-sheets/<slug>/`.
- **The PDF lives at `reference-sheets/<slug>/<slug>.pdf`.** The filename is the slug,
  so a revision replaces the file in place and never mints a second URL.
- **The page carries the sheet's content as HTML.** The PDF is the take-away download,
  never the only copy of the content.
- **The page `<title>` leads with the sheet's own printed name** — the same name printed
  on the sheet itself — with no suffix beyond the site's existing ` | Transitrix`.
- **No gate of any kind.** No form, no email field, no sign-up, no interstitial, no
  tracking wall, on the index or on any sheet page.
- **`SHA256SUMS`** lists every committed PDF's checksum, one `<sha256>  <slug>/<slug>.pdf`
  line per sheet (`sha256sum` output format). It is updated in the same commit as the
  PDF it describes.
