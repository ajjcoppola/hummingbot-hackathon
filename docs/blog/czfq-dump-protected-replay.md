# Appendix: naked vs dump-protected on Cup window

Offline replay of the Cup shadow equity hours (`data/cup_race_autotimer/equity_48h.json`)
with dump-protected v1 rules: **40% USDC sleeve**, **60% LP** tracking the naked path
until **−3%** book equity, then flatten to USDC.

LP sleeve scaled from naked Cup MTM path; does not credit USDC-heavy offset fee/IL differences. Constant-TVL / same-path approximation.

## Summary

| Arm | Close | Return |
|-----|-------|--------|
| Hold USDC | $158.08 | +0.00% |
| Naked 16% LP (actual Cup) | $147.59 | -6.64% |
| Dump-protected v1 (sleeve+kill) | $152.61 | -3.46% |

- Open book: **$158.08**; kill line: **$153.34** (−3%).
- Kill fired at hour **37.53** (book ≈ $152.61).
- Improvement vs naked: **+3.18** percentage points (still vs hold-USDC if kill fires after a loss).

Parent post: [`czfq-dump-protected-postmortem.md`](czfq-dump-protected-postmortem.md).
