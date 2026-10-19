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

**Work for this repository is filed in [`transitrix/transitrix-hq`](https://github.com/transitrix/transitrix-hq)** (a private repository), not in this repository's issue tracker. If you'd like to propose a change, report a problem, or request a feature, open a pull request here or email `hello@transitrix.com`.

## Consumer website artifact

The publish gate builds an exact reader-facing tree from the **Consumer artifact**
section of `MANIFEST.md`, validates local page and stylesheet dependencies, and
uploads `site-consumer-preview`. Build locally without deployment:

```sh
python3 .github/scripts/build_site.py --output /tmp/transitrix-site-preview
```

The output path must not exist. Reader URLs and included file bytes are preserved;
security contact, discovery files, downloads, domain markers and licensing remain.
Contributor scripts, templates, tests, workflows and source-only assets stay in the
public repository. Their exact paths remain covered by the repository inventory.
Uploading this preview does not change the Pages source or live publication.
A legacy repository-root source also serves some repository-only paths; select
GitHub Actions and perform a verified manual deployment to publish only the
consumer artifact.

## Manual publication

`Deploy consumer website manually` runs only through `workflow_dispatch` on main.
It repeats the publication tests, builds the consumer directory and verifies a
regular-file `artifact.tar` before deploying through the existing `github-pages`
environment. It never deploys on pull requests or pushes. Only the deploy job has
Pages/OIDC write permissions; the standard Ubuntu runner uses no dependency cache
and retains its small Pages artifact for one day.

The tar packager preserves exact declared dot paths, including security.txt and
the static-host marker. It rejects missing/extra/changed content and links.
Activating this workflow requires selecting GitHub Actions as the Pages source;
this does not change DNS, custom-domain or HTTPS settings. Until that source change
is explicitly applied, legacy root publication remains active.

After a completed manual deployment, verify the selected artifact and public
responses from a clean checkout of its exact SHA:

```sh
python3 .github/scripts/check_live_site.py --run-id RUN_ID --artifact-id ARTIFACT_ID \
  --environment-deployment-id ENVIRONMENT_DEPLOYMENT_ID \
  --pages-deployment-id PAGES_DEPLOYMENT_ID --output /tmp/site-acceptance.json
```

Use the artifact and Pages deployment identifiers from the deployment log and
the corresponding `github-pages` environment record. The read-only verifier uses
existing `gh` access to bind the identifiers to a successful manual main run,
downloads that exact artifact, verifies all 58 archived file hashes, and requires
all 58 public files to return matching bytes. It also checks the exact 16 legacy
repository-only URLs for HTTP 404 and requires `text/plain` for security.txt.
Redirects, HTTP errors, fallback responses and changed bytes fail acceptance.
The JSON receipt records identifiers, hashes and selected cache/request headers;
keep it outside the checkout. A successful workflow alone is not public acceptance.
This command does not deploy or change hosting settings.
