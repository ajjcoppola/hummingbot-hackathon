# Publishing the Cup letter

Canonical text: [`docs/blog/in-and-out-orca-cup.md`](../blog/in-and-out-orca-cup.md).

```bash
python3 scripts/publish_report.py
```

That rewrites four drafts in this folder. It does not post.

| Channel | Draft | How it actually goes out |
|---------|--------|--------------------------|
| Substack (investitnow) | `substack.md` | No official write API. Paste or import into the Substack editor. Canonical URL. |
| Medium (ajjcoppola.medium.com) | `medium.md` | `MEDIUM_INTEGRATION_TOKEN` if you still have a legacy token. Medium stopped issuing new tokens, so new accounts paste the draft. `--post` creates a **draft**, not a public post. |
| LinkedIn | `linkedin.txt` | `LINKEDIN_ACCESS_TOKEN` plus `LINKEDIN_AUTHOR_URN` (`urn:li:person:…`) with `w_member_social`. |
| X (@alananjcoppola) | `x_thread.txt` | Needs OAuth 1.0a user tokens (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`). A bearer token cannot post. The signer is not bundled; paste the thread until it is. |

```bash
python3 scripts/publish_report.py --post
```

Missing tokens are skipped. Nothing in this folder is a secret. Do not commit tokens.
