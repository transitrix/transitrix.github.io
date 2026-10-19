# Public repository and consumer website declaration

## Consumer artifact

The website artifact contains reader-facing HTML pages and linked downloads;
CSS, JavaScript and images used by those pages; font licensing for the embedded PDF fonts; crawler
and model discovery files; domain/static-host markers; and the security contact.
Exact paths preserve their current URLs and bytes. Font files, unused still-image
source and canonical head templates remain available to contributors in the
repository; pages use remote font CSS and inline head tags. No directory entry
admits future files.

- `.nojekyll`
- `.well-known/security.txt`
- `CNAME`
- `assets/css/style.css`
- `assets/fonts/ibm-plex/OFL.txt`
- `assets/img/apple-touch-icon.png`
- `assets/img/dsm-one-model-three-dates.png`
- `assets/img/favicon-128.png`
- `assets/img/favicon-16.png`
- `assets/img/favicon-32.png`
- `assets/img/studio-preview.gif`
- `assets/img/transitrix-icon.svg`
- `assets/js/theme.js`
- `assets/og/transitrix-og.png`
- `de/dsl-examples/index.html`
- `de/dsm/index.html`
- `de/index.html`
- `de/install/index.html`
- `de/quickstart/index.html`
- `de/recipes/index.html`
- `de/strategy-and-behaviour/index.html`
- `de/ttrs/index.html`
- `do-i-need-dsm/index.html`
- `dsl-examples/index.html`
- `dsm/index.html`
- `enterprise-as-text/index.html`
- `explainers/SHA256SUMS`
- `explainers/how-a-document-prints/how-a-document-prints.pdf`
- `explainers/how-a-document-prints/index.html`
- `explainers/how-the-repository-works/index.html`
- `explainers/index.html`
- `favicon.ico`
- `index.html`
- `install/go/claude/index.html`
- `install/go/jetbrains/index.html`
- `install/go/openvsx/index.html`
- `install/go/vscode/index.html`
- `install/index.html`
- `is-it-open-source/index.html`
- `learn/index.html`
- `library/SHA256SUMS`
- `library/archimate-cheat-sheet/archimate-cheat-sheet.pdf`
- `library/archimate-cheat-sheet/index.html`
- `library/index.html`
- `llms.txt`
- `marketplace-status/index.html`
- `methodology/index.html`
- `quickstart/index.html`
- `recipes/index.html`
- `repository-mcp/index.html`
- `robots.txt`
- `sitemap.xml`
- `strategy-and-behaviour/index.html`
- `ttrs/index.html`
- `vs-drawing-tools/index.html`
- `what-can-i-model/index.html`
- `what-is-transitrix/index.html`
- `which-editor/index.html`

## Repository-only files

The public developer repository also carries validators, generation scripts and
workflows needed to maintain the site; exact inventory and packaging controls;
and contributor/curator instructions. They are not part of the website artifact.
The existing legacy Pages root still serves some of them until publication is
explicitly switched to the verified artifact. This declaration does not deploy it.

- `.github/dependabot.yml`
- `.github/pull_request_template.md`
- `.github/scripts/build_site.py`
- `.github/scripts/check_publish_manifest.py`
- `.github/scripts/test_publish_manifest.py`
- `.github/scripts/test_site_artifact.py`
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
- `MANIFEST.md`
- `README.md`
- `library/README.md`
- `scripts/check_explainers.py`
- `scripts/check_library.py`
- `scripts/generate_sitemap.py`
- `assets/fonts/ibm-plex/IBMPlexMono-Medium.woff2`
- `assets/fonts/ibm-plex/IBMPlexMono-Regular.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Bold.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Medium.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-Regular.woff2`
- `assets/fonts/ibm-plex/IBMPlexSans-SemiBold.woff2`
- `assets/img/studio-preview.png`
- `assets/inc/favicon-links.html`
- `assets/inc/og-meta.html`
