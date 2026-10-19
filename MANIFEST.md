# Published files declaration — transitrix.github.io

**Last updated:** 2026-10-19

This file declares exact paths admitted to the public repository. The full tracked tree is checked. GitHub Pages currently serves the root of main with .nojekyll; scripts and repository documentation below are also directly reachable. This inventory preserves existing content as-is and does not change deployment.

## HTML pages

- `index.html` — English homepage (root)
- `de/index.html` — German homepage
- `de/dsl-examples/index.html` — German DSL examples
- `de/dsm/index.html` — German DSM page
- `de/install/index.html` — German install page
- `de/quickstart/index.html` — German quickstart
- `de/recipes/index.html` — German recipes
- `de/strategy-and-behaviour/index.html` — German strategy and behaviour
- `de/ttrs/index.html` — German TTRS
- `do-i-need-dsm/index.html` — Do I need DSM
- `dsl-examples/index.html` — DSL examples
- `dsm/index.html` — DSM page
- `enterprise-as-text/index.html` — Enterprise as text
- `explainers/index.html` — Explainers hub
- `explainers/how-the-repository-works/index.html` — How the repository works
- `install/index.html` — Install page
- `install/go/claude/index.html` — Install Claude link
- `install/go/jetbrains/index.html` — Install JetBrains link
- `install/go/openvsx/index.html` — Install OpenVSX link
- `install/go/vscode/index.html` — Install VS Code link
- `is-it-open-source/index.html` — Is it open source
- `learn/index.html` — Learning hub
- `library/index.html` — Library page
- `library/archimate-cheat-sheet/index.html` — ArchiMate cheat sheet HTML
- `marketplace-status/index.html` — Marketplace status and release verification
- `methodology/index.html` — Methodology page
- `quickstart/index.html` — Quickstart page
- `recipes/index.html` — Recipes page
- `repository-mcp/index.html` — Governed enterprise model access explainer
- `strategy-and-behaviour/index.html` — Strategy and behaviour page
- `ttrs/index.html` — TTRS page
- `vs-drawing-tools/index.html` — Vs drawing tools
- `what-can-i-model/index.html` — What can I model
- `what-is-transitrix/index.html` — What is Transitrix
- `which-editor/index.html` — Which editor

## Stylesheets and theme

- `assets/css/style.css` — Main stylesheet (light and dark themes)
- `assets/js/theme.js` — Theme toggle script

## Fonts

- `assets/fonts/ibm-plex/IBMPlexMono-Medium.woff2`
- `assets/fonts/ibm-plex/IBMPlexMono-Regular.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Bold.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Medium.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Regular.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-SemiBold.woff2`
- `assets/fonts/ibm-plex/OFL.txt` — Font licence

## Images

- `assets/img/apple-touch-icon.png`
- `assets/img/dsm-one-model-three-dates.png`
- `assets/img/favicon-128.png`
- `assets/img/favicon-16.png`
- `assets/img/favicon-32.png`
- `assets/img/studio-preview.gif`
- `assets/img/studio-preview.png`
- `assets/img/transitrix-icon.svg`
- `assets/og/transitrix-og.png` — Open Graph image
- `favicon.ico` — Favicon (root)

## Site metadata and configuration

- `CNAME` — Domain name configuration
- `.nojekyll` — Jekyll disable marker
- `.well-known/security.txt` — Security policy
- `robots.txt` — Robot crawler directives
- `sitemap.xml` — XML sitemap
- `llms.txt` — LLM-accessible content index

## HTML includes (rendered as part of pages)

- `assets/inc/favicon-links.html` — Favicon link tags
- `assets/inc/og-meta.html` — Open Graph meta tags

## Documents and downloads

- `explainers/how-a-document-prints/how-a-document-prints.pdf` — Explainer PDF
- `explainers/SHA256SUMS` — Checksum file for explainers
- `library/archimate-cheat-sheet/archimate-cheat-sheet.pdf` — ArchiMate cheat sheet PDF
- `library/SHA256SUMS` — Checksum file for library

## Additional files served from the current Pages root

- `MANIFEST.md`
- `README.md`
- `explainers/how-a-document-prints/index.html`
- `library/README.md`
- `scripts/check_explainers.py`
- `scripts/check_library.py`
- `scripts/generate_sitemap.py`

## Repository machinery and metadata

These exact paths are admitted to the repository; no directory entry admits future files.

- `.github/dependabot.yml`
- `.github/pull_request_template.md`
- `.github/scripts/check_publish_manifest.py`
- `.github/scripts/test_publish_manifest.py`
- `.github/workflows/dependabot-auto-merge.yml`
- `.github/workflows/explainers.yml`
- `.github/workflows/icon-declarations.yml`
- `.github/workflows/indexing-declarations.yml`
- `.github/workflows/library.yml`
- `.github/workflows/methodology-version-check.yml`
- `.github/workflows/og-declarations.yml`
- `.github/workflows/public-surface-hygiene.yml`
- `.github/workflows/publish-gate.yml`
- `.github/workflows/simple-pr-automerge.yml`
- `.gitignore`

Every tracked path must be declared. New or existing undeclared paths fail the gate, independently of diff context.
