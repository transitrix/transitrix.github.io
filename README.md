# transitrix.com

Source for [transitrix.com](https://transitrix.com) — the marketing and documentation site for the Transitrix product family.

Built with plain HTML/CSS, served via GitHub Pages.

Canonical, schema-valid YAML examples for every Transitrix notation live at [`/dsl-examples/`](dsl-examples/index.html) — see also [`llms.txt`](llms.txt) for a machine-readable project summary.

`sitemap.xml` is generated, not hand-maintained — after adding, removing or renaming a page, run `python3 scripts/generate_sitemap.py > sitemap.xml`. CI fails if the committed file doesn't match.

## Development

Open `index.html` directly in a browser, or serve locally:

```
npx serve .
```

## Contributing

Content changes go through pull requests. Routine updates are handled by automation.

**Work for this repository is filed in [`transitrix/transitrix-hq`](https://github.com/transitrix/transitrix-hq)**, not in this repository's issue tracker. Open an issue there to propose a change, report a problem, or request a feature.
