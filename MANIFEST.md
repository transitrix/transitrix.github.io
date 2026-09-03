# Published files declaration — transitrix.github.io

**Last updated:** 2026-09-02

This file declares the published artefacts served by transitrix.github.io (the transitrix.com website). A file served to a reader is listed below. Internal machinery, source files, and build artifacts are not published and are not listed.

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
- `methodology/index.html` — Methodology page
- `quickstart/index.html` — Quickstart page
- `recipes/index.html` — Recipes page
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

## Not published

- Source and generation scripts (`scripts/`)
- Workflows and build configuration (`.github/`)
- Repository documentation (`.gitignore`, `README.md`)
- Internal-only documents (`CLAUDE.md`, `STRATEGIC_BRIEF.md`, etc. — see `.gitignore`)

---

A pull request that adds or modifies a file not in this list will fail the publication gate and not merge.
