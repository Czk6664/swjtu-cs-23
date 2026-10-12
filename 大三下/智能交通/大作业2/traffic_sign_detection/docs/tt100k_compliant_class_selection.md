# TT100K Compliant Class Selection

This project phase uses the top 12 TT100K source categories by raw object count in `annotations_all.json`.
The final training names intentionally preserve the original TT100K code in normalized form (`tt100k_<code>`) to avoid assigning incorrect semantic translations to dataset-specific category codes.

| Rank | Source category | Normalized class name | Raw objects | Raw images |
|---:|---|---|---:|---:|
| 1 | pn | tt100k_pn | 3176 | 3016 |
| 2 | pne | tt100k_pne | 2384 | 2142 |
| 3 | i5 | tt100k_i5 | 1734 | 1599 |
| 4 | p11 | tt100k_p11 | 1582 | 1560 |
| 5 | pl40 | tt100k_pl40 | 1413 | 1376 |
| 6 | pl50 | tt100k_pl50 | 1073 | 1062 |
| 7 | pl80 | tt100k_pl80 | 904 | 827 |
| 8 | p26 | tt100k_p26 | 840 | 786 |
| 9 | pl60 | tt100k_pl60 | 835 | 803 |
| 10 | i4 | tt100k_i4 | 814 | 774 |
| 11 | pl100 | tt100k_pl100 | 673 | 394 |
| 12 | pl30 | tt100k_pl30 | 640 | 637 |

The previously configured zero-sample classes `i6`, `i7`, `i8`, and `pl6` are not counted toward the final course requirement.
