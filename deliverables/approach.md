# approach.md

Pipeline (deterministic with light heuristics)
- IPs: trim, drop zone-id, relaxed IPv4 parsing (leading zeros allowed), standard `ipaddress` validation for v4/v6, default subnets (/24 for RFC1918, /16 APIPA, /8 loopback, /64 IPv6 link-local), flag reserved .0/.255 edges, build reverse PTR for valid IPs.
- Names: lowercase hostname/FQDN, RFC label validation, derive hostname from FQDN when missing, set `fqdn_consistent` when both are present and aligned; record mismatches as anomalies.
- MACs: strip separators, require 12 hex chars, colon-normalize lowercase; otherwise flag invalid.
- Owner/team/email: extract first email, parse team from parentheses, normalize human-readable name (or fallback from email local-part).
- Device type: trust provided value (high confidence); otherwise infer from hostname/notes keywords (printer/switch/router/server/iot) with medium confidence.
- Site: trim, normalize separators, map common aliases (e.g., BLR CAMPUS, HQ BLDG 1, LAB 1, DC 1).
- All steps appended to `normalization_steps`; anomalies capture issues + recommended actions.

Reproduce end-to-end
- Prereq: Python 3.x, no external deps or network needed.
- From repo root: `python3 run.py`
- Outputs: `deliverables/inventory_clean.csv` and `deliverables/anomalies.json`

AI usage
- No live LLM calls were used due to offline constraints; heuristics simulate low-temperature decisions for ambiguous fields. The code is structured so an LLM-backed resolver can replace the heuristic functions later.
