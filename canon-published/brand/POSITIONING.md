# Positioning statement — Transitrix site source reference

**This file documents where the positioning statement lives and how this surface uses it.**

## Source of truth

The canonical positioning statement is maintained in the headquarters repository:

**Location:** `transitrix-hq/canon-published/guides/positioning.md`  
**Source commit:** 0c2315e (as of 2026-09-06 07:45 UTC)  
**Admitted:** 2026-08-31 by Valerii

The statement is **authoritative and must never be modified on this repository.** Every public surface copies from it verbatim — never paraphrased, never adapted.

## The statement (verbatim copy)

> **You leave with a decision you can keep true.** Not a report of one — the model the
> decision was made in, in your own repository, and the method to keep it current after we
> are gone.
>
> That is what **Architecture-as-Code for the enterprise** is for: the git-native,
> text-first discipline software already has, carried up to the strategy, business and
> architecture layers that code-scoped tools never reach. The enterprise is described once,
> in plain text, and every view — a goal tree, a capability map, a sequence diagram — is
> projected from that one description.
>
> **Against code-scoped tools.** Architecture-as-Code exists today and stops at software.
> The layers where the money is committed — motivation, strategy, business — are the ones it
> never reaches, and they are the ones this covers.
>
> **Against context and memory layers.** This is a formal model, not free-form notes and not
> opaque embeddings. It validates, it diffs, and a change to it is reviewed the way a change
> to code is reviewed. A machine can act on it because it is grounded, not because it was
> remembered.

## Short forms approved for surfaces with limited space

All approved short forms are prefixes of the full statement, never paraphrases. The canonical source document defines three approved forms:

| Form | Use | Text |
|---|---|---|
| **Lead sentence** | first sentence of sales conversation; hero subhead; listing opener | *"You leave with a decision you can keep true."* |
| **Two-sentence form** | listings, sheet-library footer, explainer opening, channel bio | Lead sentence + the sentence that follows it |
| **Category form** | GitHub org, methodology repo, technical listings (names what this *is* rather than what it's for) | *"Architecture-as-Code for the enterprise — the git-native, text-first discipline software already has, carried up to the strategy, business and architecture layers that code-scoped tools never reach."* |

**Contrast paragraphs are mandatory in body copy.** A surface with room for category but not for contrasts should use the lead sentence instead.

## Process for updating

1. **This file refreshes whenever the canonical statement changes.** The headquarters repository publishes a new canon slice when the statement is updated; this repository's next session refresh detects the change and re-syncs this file verbatim.

2. **Surfaces referencing this file must re-check whenever they update positioning text.** Search for "positioning" and verify every usage matches one of the approved forms above.

3. **A surface that needs different words needs a different surface, not a different statement.** Questions about whether a surface should exist — not how to phrase it — route to the Strategist.

## Constraints that bind every deployment

- `CONSTRAINT-MARKET-EXCLUSION-1`: The statement itself names no market and no client; a deployment must not add either.
- `CONSTRAINT-NO-CLIENT-NAMES-1`: No real client names or internal project codes appear in any surface using this statement.

## Related surfaces on this site

Surfaces referencing this positioning statement:
- Homepage hero section (`index.html`)
- "What is Transitrix?" page (`what-is-transitrix/index.html`)
- Channel descriptions (website footer, social media)

See `transitrix-hq#651` for the full surface update task.

---

**Source:** transitrix-hq#650 (SITE portion of epic transitrix-hq#423)  
**Maintained by:** Site project agent  
**Last refreshed:** 2026-09-07
