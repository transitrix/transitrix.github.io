# Library — contract

This directory holds the transitrix.com library of free reference material. The shape
below is enforced by `scripts/check_library.py` in CI (`.github/workflows/library.yml`)
— an item that violates it fails the check rather than reaching a reader.

- **One directory per item:** `library/<slug>/`, served at
  `https://transitrix.com/library/<slug>/`.
- **The PDF lives at `library/<slug>/<slug>.pdf`.** The filename is the slug, so a
  revision replaces the file in place and never mints a second URL.
- **The page carries the item's content as HTML.** The PDF is the take-away download,
  never the only copy of the content.
- **The page `<title>` leads with the item's own printed name** — the same name printed
  on the item itself — with no suffix beyond the site's existing ` | Transitrix`.
- **Kinds of material are not path segments.** A cheat sheet, a template and a worked
  example all sit directly under `library/<slug>/`; grouping belongs on the index page,
  where it can be revised, never in an address that has been printed and handed out.
- **No gate of any kind.** No form, no email field, no sign-up, no interstitial, no
  tracking wall, on the index or on any item page.
- **`SHA256SUMS`** lists every committed PDF's checksum, one `<sha256>  <slug>/<slug>.pdf`
  line per item (`sha256sum` output format). It is updated in the same commit as the
  PDF it describes.
