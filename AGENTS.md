# AGENTS.md — agent guide for transitrix.github.io

> This governs any coding agent working in this repository — the public source for
> [transitrix.com](https://transitrix.com), the Transitrix initiative's marketing and
> documentation site. It states generic, portable repository policy; it does not
> describe any single tool's runtime behaviour.

## 1. What this repo is

Plain HTML/CSS/JS, no build step, served by GitHub Pages. See `README.md` for local
development.

- **English pages** live at the repo root; **German pages** mirror them under `/de/`.
  No other languages.
- `library/` — the free reference library (PDFs and their served HTML pages); its own
  shape and constraints are documented in `library/README.md`.
- `sitemap.xml` is generated: after adding, removing or renaming a page, regenerate it
  (`python3 scripts/generate_sitemap.py > sitemap.xml`) — CI fails if the committed
  file doesn't match.

## 2. Contribution flow

1. Branch from `main`, one concern per PR.
2. Open a pull request; **do not merge it** — a maintainer reviews and merges. One
   exception is already wired in `.github/workflows/dependabot-auto-merge.yml`: a
   green, non-major Dependabot PR merges itself. That grant does not extend to any
   other PR.
3. Conventional Commits for commit subjects and PR titles (`type(scope): subject` —
   `site:`, `chore:`, `fix:`, `docs:`).
4. Fill in both sections of `.github/pull_request_template.md`: what changed, how it's
   verified.

## 3. CI, and what it enforces

Every PR runs the workflows under `.github/workflows/`:

- **Icon declarations** — every page declares the site's icon set from the canonical
  partial.
- **Indexing declarations** — every page listed in `sitemap.xml` has an absolute,
  self-matching `rel="canonical"` and is reachable from the homepage.
- **OG declarations** — every sitemap page has a complete, self-consistent OG/Twitter
  metadata block.
- **Library** — `library/` holds to its documented shape and no-gate contract
  (`library/README.md`).
- **Public-surface hygiene** — see §4; this is the one most likely to fail a change
  that otherwise looks correct.

Each check reads only committed files, so it's reproducible locally from its workflow
source before you open a PR.

## 4. Public-surface discipline — read this before committing

**This repository and the site it serves are both fully public.** Commit messages, PR
titles and bodies, issue comments, and every committed file are permanently visible and
indexed. Write and commit as though nothing here can later be made private.

- **A public surface carries what its reader needs, and nothing else.** Before adding a
  file, name who reads it *from this repository* and what breaks for them if it's
  absent. If the only consumer is this repository's own tooling and the file could live
  elsewhere, it doesn't belong here. Where a deliverable is produced from a source (the
  `library/` PDF-from-source pattern is the example already in this repo), the surface
  carries the deliverable; the source, the renderer, and any verification apparatus
  covering more than the published artefact stay off the public surface unless the
  platform genuinely forces them here.
- **No pointer to anything private.** Never commit a link, path fragment, folder name,
  or document title that only resolves inside a private system, and never cite a
  private work item by number in committed content — commit messages included, since a
  squash-merged PR title becomes a commit subject. A private decision, if it needs
  citing, is cited by name and date, never by link or number.
  `.github/workflows/public-surface-hygiene.yml` scans for this on every push and PR;
  treat a failure there as a real finding, not something to route around.
- **No internal-only file at the repository root.** In particular, **never commit
  `CLAUDE.md`** — that name is reserved for a private, gitignored, tool-specific
  coordination file. This `AGENTS.md` is the canonical, tracked guide for this
  repository; `.github/workflows/public-surface-hygiene.yml` enforces the ban on
  committing `CLAUDE.md`.
- **No real client/customer name and no internal project code** in any committed
  content — refer to work generically.
- When in doubt whether something belongs on this surface, leave it out and ask in the
  PR description rather than commit it and find out from a failed check.

## 5. What NOT to do

- Do not merge your own PR.
- Do not commit `CLAUDE.md`, or any other tool-specific coordination file, at the
  repository root.
- Do not hand-edit `sitemap.xml` — regenerate it (§1).
- Do not add a check that re-renders and diffs a `library/` PDF to verify it's current
  — see `library/README.md` for why that doesn't work.
- Do not introduce a hard sales CTA (waitlist, pricing, "book a demo") — the site's
  affordances stay to install / read / quickstart.
