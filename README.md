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

To propose a change, open a pull request. To report a problem or request a feature, email `hello@transitrix.com`.

## Consumer website artifact

The publish gate builds an exact reader-facing tree from the **Consumer artifact**
section of `MANIFEST.md`, validates local page and stylesheet dependencies, and
uploads `site-consumer-preview`. Build locally without deployment:

```sh
python3 .github/scripts/build_site.py --output /tmp/transitrix-site-preview
```

The output path must not exist. `MANIFEST.md` declares the website files and
repository-only contributor tools separately. The preview includes only the
website files; generating or uploading it does not publish the site.

## Manual publication

Run `Deploy consumer website manually` from main with GitHub Actions selected as
the Pages source. The workflow tests, builds and verifies the website archive
before deployment. Pushes and pull requests do not trigger this workflow.

After a completed manual deployment, verify the selected artifact and public
responses from a clean checkout of its exact SHA:

```sh
python3 .github/scripts/check_live_site.py --run-id RUN_ID --artifact-id ARTIFACT_ID \
  --environment-deployment-id ENVIRONMENT_DEPLOYMENT_ID \
  --pages-deployment-id PAGES_DEPLOYMENT_ID --output /tmp/site-acceptance.json
```

Use identifiers from the deployment log and the corresponding `github-pages`
environment record. The verifier requires existing `gh` access. It checks the
selected artifact, exact public file bytes, security.txt content type, and HTTP
404 responses for excluded repository-only paths. It writes a JSON receipt to
the output path. A successful workflow alone does not establish public acceptance.
