---
name: review-shadlet-code
description: Review proposed Shadlet changes for correctness, security, compatibility, accessibility, and test gaps. Use when reviewing a diff or pull request; report actionable findings with file and symbol references.
---

# Review Shadlet changes

Review the diff for user-visible defects and evidence-backed risks. Report findings first, ordered by severity, with file and symbol/line references; avoid speculative style comments.

## Review checklist

- Does the Python API, runtime schema, protocol v2 payload, and TypeScript renderer agree? Are malformed or unknown inputs rejected clearly?
- Are handlers, state updates, cancellation, session isolation, routing, and cleanup correct under reconnects and concurrent events?
- Are paths, uploads, storage, extension assets, URLs, and client-facing errors safe at the relevant trust boundary?
- Are controls actually interactive, semantically labeled, keyboard operable, focus-correct, theme-compatible, and responsive?
- Are changes backward-compatible or accompanied by a precise migration note?
- Do tests exercise public behavior and failure cases? Are screenshots/visual results claimed only if reviewed?
- Do docs, examples, templates, changelog, package metadata, and generated assets match the code?

Do not report a finding without pointing to the changed code and explaining a concrete failure or impact. Note testing gaps separately from confirmed defects. Do not edit files during a review unless asked to fix findings.

## References

- `docs/architecture/protocol.md`
- `docs/architecture/security.md`
- `docs/development/testing.md`
- `docs/limitations.md`
