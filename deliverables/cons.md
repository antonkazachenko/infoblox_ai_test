# cons.md
- Device type inference is keyword-only; nuanced roles (firewall vs router, hypervisor vs server) are not distinguished without richer signals or an LLM.
- Owner parsing assumes a single contact with an optional email and parenthesized team; multiple owners or unconventional text may be missed.
- Subnet defaults (/24 private IPv4, /64 IPv6 link-local) are coarse heuristics and may not match actual network design.
- FQDN validation is syntactic only; no DNS resolution or split-horizon handling in the offline environment.
- MAC validation rejects anything not 12 hex digits; vendor lookup/OUI enrichment is not performed.
