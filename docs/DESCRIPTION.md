# Infoblox – AI Skills test

## Assignment Title
**Data Cleaning and Validation for Network Inventory Records**

## Background
[cite_start]Infoblox’s core products manage DNS, DHCP, and IP Address Management (DDI) data at scale[cite: 6]. [cite_start]Clean, consistent network data is critical for automation and insight[cite: 7].

[cite_start]In this challenge, you’ll simulate building an intelligent data-cleaning assistant that validates and normalizes a small, messy dataset representing network inventory[cite: 8]. [cite_start]You’ll apply both deterministic rules and AI reasoning to demonstrate your problem-solving approach[cite: 9].

## Objective
[cite_start]Transform the provided `inventory_raw.csv` into a cleaned and normalized `inventory_clean.csv` suitable for downstream IPAM/DNS workflows[cite: 11].

[cite_start]You’ll validate, normalize, enrich, and flag anomalies using your own rules and optionally an LLM of your choice[cite: 12]. [cite_start]You are allowed to use an LLM to generate the code as well if you wish to do so[cite: 13].

> **Note:** Watch out for bugs in the generated code. [cite_start]If you are unclear on any of the requirements, feel free to clarify using an LLM[cite: 14].

## Files Provided
* [cite_start]**inventory_raw.csv** – Synthetic, intentionally messy dataset[cite: 16].
* [cite_start]**run_ipv4_validation.py.txt** – Example IPv4 validation logic[cite: 16].
* [cite_start]**TEMPLATES/** – Folder with empty templates to fill[cite: 16]:
    * `prompts.md` – record of prompts and iterations
    * `approach.md` – your pipeline description
    * `cons.md` – known limitations or risks
* [cite_start]**run.py.txt** – simple orchestrator to extend with your logic[cite: 16].
* [cite_start]**README.md** – schema and reference info[cite: 16].

## Tasks

### Validation
[cite_start]For each record, validate and normalize key fields: IP address, MAC address, hostname, FQDN, owner, device type, and site[cite: 19]. [cite_start]Add flags like `ip_valid`, `hostname_valid`, `fqdn_consistent`, and `device_type_confidence` where relevant[cite: 20].

### Normalization
Apply deterministic transformations—lowercasing, trimming, deduplication, and canonicalization. [cite_start]Derive fields like `subnet_cidr` and `reverse_ptr` for valid IPs[cite: 22].

### Anomaly Reporting
[cite_start]Generate `anomalies.json` listing row ID, affected field(s), issue type, and recommended action[cite: 24].

### AI Involvement
Use an LLM to resolve ambiguous cases (e.g., unclear `device_type` or owner). [cite_start]Record every prompt in `prompts.md` along with rationale[cite: 26]. [cite_start]Keep temperature low (≤ 0.2) and outputs structured (JSON preferred)[cite: 27].

### Limitations & Reflection
[cite_start]In `cons.md`, describe at least three limitations or trade-offs (e.g., model hallucination risk, missing external context, split-horizon FQDN unmodeled)[cite: 29].

### Reproducibility
[cite_start]Provide a single entry point (`run.py` or `run.sh`) that regenerates `inventory_clean.csv` and `anomalies.json`[cite: 31].

## Expected Output Schema
[cite_start]The following table[cite: 33]:

| Column | Description |
| :--- | :--- |
| `ip`, `ip_valid`, `ip_version`, `subnet_cidr` | IP fields and validity |
| `hostname`, `hostname_valid`, `fqdn`, `fqdn_consistent`, `reverse_ptr` | Naming validation |
| `mac`, `mac_valid` | MAC normalization |
| `owner`, `owner_email`, `owner_team` | Ownership parsing |
| `device_type`, `device_type_confidence` | Classification |
| `site`, `site_normalized` | Site normalization |
| `source_row_id`, `normalization_steps` | Traceability |

## Submission Package
[cite_start]Zip and submit the following files[cite: 35]:

1.  [cite_start]`inventory_clean.csv` [cite: 36]
2.  [cite_start]`anomalies.json` [cite: 37]
3.  [cite_start]`prompts.md` [cite: 38]
4.  [cite_start]`approach.md` [cite: 39]
5.  [cite_start]`cons.md` [cite: 40]
6.  [cite_start]`run.py` or `run.sh` [cite: 41]

[cite_start]Alternatively, you may create a Github repo and share the link with us[cite: 42].

## Final Notes
[cite_start]We’re not scoring for perfection—focus on clear reasoning, reproducibility, and awareness of trade-offs[cite: 44]. [cite_start]Show us how you balance deterministic logic with responsible use of AI[cite: 45].