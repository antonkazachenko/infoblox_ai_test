#!/usr/bin/env python3
"""
Infoblox AI Skills Test - Data Cleaning Orchestrator

Deterministic-first pipeline with light heuristics for ambiguous fields.
Generates deliverables/inventory_clean.csv and deliverables/anomalies.json.
"""

from __future__ import annotations

import csv
import ipaddress
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
HOST_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)

FIELDNAMES = [
    "ip",
    "ip_valid",
    "ip_version",
    "subnet_cidr",
    "hostname",
    "hostname_valid",
    "fqdn",
    "fqdn_consistent",
    "reverse_ptr",
    "mac",
    "mac_valid",
    "owner",
    "owner_email",
    "owner_team",
    "device_type",
    "device_type_confidence",
    "site",
    "site_normalized",
    "source_row_id",
    "normalization_steps",
]


@dataclass
class CleanRecord:
    ip: str = ""
    ip_valid: str = ""
    ip_version: str = ""
    subnet_cidr: str = ""
    hostname: str = ""
    hostname_valid: str = ""
    fqdn: str = ""
    fqdn_consistent: str = ""
    reverse_ptr: str = ""
    mac: str = ""
    mac_valid: str = ""
    owner: str = ""
    owner_email: str = ""
    owner_team: str = ""
    device_type: str = ""
    device_type_confidence: str = ""
    site: str = ""
    site_normalized: str = ""
    source_row_id: str = ""
    normalization_steps: str = ""


def uniq(seq: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in seq:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def classify_ipv4_type(ip_obj: ipaddress.IPv4Address) -> str:
    first, second = ip_obj.packed[0], ip_obj.packed[1]
    if first == 10 or (first == 172 and 16 <= second <= 31) or (first == 192 and second == 168):
        return "private_rfc1918"
    if first == 169 and second == 254:
        return "link_local_apipa"
    if first == 127:
        return "loopback"
    return "public_or_other"


def default_subnet(ip_obj: ipaddress._BaseAddress) -> str:
    if isinstance(ip_obj, ipaddress.IPv4Address):
        ipv4_type = classify_ipv4_type(ip_obj)
        if ipv4_type == "private_rfc1918":
            parts = str(ip_obj).split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        if ipv4_type == "link_local_apipa":
            return "169.254.0.0/16"
        if ipv4_type == "loopback":
            return "127.0.0.0/8"
        return ""
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.is_link_local:
        return str(ipaddress.IPv6Network(f"{ip_obj.compressed}/64", strict=False))
    return ""


def parse_ipv4_relaxed(candidate: str):
    parts = candidate.split(".")
    if len(parts) != 4:
        return None
    canonical_parts: List[str] = []
    for part in parts:
        if part == "":
            return None
        if not (part.lstrip("+").isdigit() and not part.startswith("-")):
            return None
        try:
            value = int(part, 10)
        except ValueError:
            return None
        if value < 0 or value > 255:
            return None
        canonical_parts.append(str(value))
    try:
        return ipaddress.IPv4Address(".".join(canonical_parts))
    except ValueError:
        return None


def normalize_ip(ip_str) -> Tuple[str, str, str, str, List[str], List[Dict]]:
    steps: List[str] = []
    issues: List[Dict] = []
    if ip_str is None:
        steps.append("ip_missing")
        issues.append({"field": "ip", "type": "missing", "value": ""})
        return "", "false", "", "", steps, issues

    raw = str(ip_str).strip()
    steps.append("ip_trim")
    if raw.lower() in {"n/a", "na", "none", ""}:
        steps.append("ip_missing")
        issues.append({"field": "ip", "type": "missing", "value": raw})
        return raw, "false", "", "", steps, issues

    candidate = raw
    if "%" in candidate:
        candidate = candidate.split("%", 1)[0]
        steps.append("ip_drop_zone")

    try:
        ip_obj = ipaddress.ip_address(candidate)
    except ValueError as exc:
        relaxed = parse_ipv4_relaxed(candidate)
        if relaxed:
            ip_obj = relaxed
            steps.append("ip_parse_relaxed")
        else:
            steps.append("ip_invalid_parse")
            issues.append({"field": "ip", "type": "invalid", "value": raw, "detail": str(exc)})
            return raw, "false", "", "", steps, issues

    ip_out = ip_obj.compressed
    steps.extend(["ip_parse", "ip_normalize"])
    ip_version = str(ip_obj.version)
    subnet = default_subnet(ip_obj)

    if isinstance(ip_obj, ipaddress.IPv4Address) and classify_ipv4_type(ip_obj) == "private_rfc1918":
        last_octet = int(str(ip_obj).split(".")[3])
        if last_octet in {0, 255}:
            steps.append("ip_reserved_edge")
            issues.append({"field": "ip", "type": "reserved_edge", "value": raw})

    return ip_out, "true", ip_version, subnet, steps, issues


def valid_label(label: str) -> bool:
    return bool(HOST_LABEL_RE.match(label))


def normalize_names(hostname_raw, fqdn_raw) -> Tuple[str, str, str, str, List[str], List[Dict]]:
    steps: List[str] = []
    issues: List[Dict] = []
    hostname = hostname_raw.strip() if hostname_raw else ""
    fqdn = fqdn_raw.strip() if fqdn_raw else ""
    hostname_valid = ""
    fqdn_consistent = ""

    if hostname:
        steps.append("hostname_trim")
        hostname = hostname.lower()
        steps.append("hostname_lower")
        hostname_valid = "true" if valid_label(hostname) else "false"
        if hostname_valid == "false":
            issues.append({"field": "hostname", "type": "invalid_label", "value": hostname_raw})

    fqdn_labels: List[str] = []
    fqdn_out = ""
    if fqdn:
        steps.append("fqdn_trim")
        fqdn_out = fqdn.lower()
        steps.append("fqdn_lower")
        fqdn_labels = fqdn_out.split(".")
        fqdn_valid = len(fqdn_labels) >= 2 and all(valid_label(l) for l in fqdn_labels)
        if not fqdn_valid:
            issues.append({"field": "fqdn", "type": "invalid_format", "value": fqdn_raw})
    else:
        fqdn_valid = False

    if not hostname and fqdn_valid:
        hostname = fqdn_labels[0]
        hostname_valid = "true"
        steps.append("hostname_from_fqdn")

    if hostname and fqdn_out:
        if fqdn_valid and fqdn_labels:
            fqdn_consistent = "true" if hostname == fqdn_labels[0] else "false"
            if fqdn_consistent == "false":
                issues.append({"field": "fqdn", "type": "hostname_mismatch", "value": fqdn_raw})
        else:
            fqdn_consistent = "false"

    return hostname, hostname_valid, fqdn_out, fqdn_consistent, steps, issues


def normalize_mac(mac_raw) -> Tuple[str, str, List[str], List[Dict]]:
    steps: List[str] = []
    issues: List[Dict] = []
    if mac_raw is None or str(mac_raw).strip() == "":
        steps.append("mac_missing")
        return "", "", steps, issues

    steps.append("mac_trim")
    mac_str = str(mac_raw).strip()
    hex_only = re.sub(r"[^0-9A-Fa-f]", "", mac_str)
    if len(hex_only) == 12 and re.fullmatch(r"[0-9A-Fa-f]{12}", hex_only):
        steps.extend(["mac_hex_extract", "mac_normalize"])
        mac_out = ":".join(hex_only[i : i + 2] for i in range(0, 12, 2)).lower()
        return mac_out, "true", steps, issues

    issues.append({"field": "mac", "type": "invalid_mac", "value": mac_raw})
    return mac_str, "false", steps, issues


def parse_owner(owner_raw) -> Tuple[str, str, str, List[str]]:
    steps: List[str] = []
    if owner_raw is None:
        return "", "", "", steps
    owner = str(owner_raw).strip()
    if not owner:
        return "", "", "", steps

    steps.append("owner_trim")
    emails = EMAIL_RE.findall(owner)
    owner_email = emails[0].lower() if emails else ""
    if owner_email:
        steps.append("owner_email_extract")
        owner = owner.replace(owner_email, "").strip()

    team = ""
    team_match = re.search(r"\\(([^)]+)\\)", owner)
    if team_match:
        team = team_match.group(1).strip()
        steps.append("owner_team_paren")
        owner = re.sub(r"\\([^)]+\\)", "", owner).strip()

    owner_name = owner.strip()
    if not owner_name and owner_email:
        owner_name = owner_email.split("@")[0].replace(".", " ").replace("_", " ")
        steps.append("owner_from_email_localpart")

    if not owner_name and team and not owner_email:
        return "", "", team.title(), steps

    owner_clean = " ".join(word.capitalize() for word in owner_name.split()) if owner_name else ""
    team_clean = team.title() if team else ""
    return owner_clean, owner_email, team_clean, steps


def normalize_device_type(raw_value, hostname: str, notes: str) -> Tuple[str, str, List[str]]:
    steps: List[str] = []
    if raw_value:
        steps.append("device_from_input")
        return str(raw_value).strip().lower(), "high", steps

    inferred = ""
    hints = (hostname or "").lower() + " " + (notes or "").lower()
    if "printer" in hints:
        inferred = "printer"
    elif "switch" in hints:
        inferred = "switch"
    elif "router" in hints or "gateway" in hints or "gw" in hints:
        inferred = "router"
    elif "cam" in hints or "iot" in hints:
        inferred = "iot"
    elif "srv" in hints or "server" in hints or "db" in hints:
        inferred = "server"

    if inferred:
        steps.append("device_inferred")
        return inferred, "medium", steps

    return "", "", steps


def normalize_site(site_raw) -> Tuple[str, str, List[str]]:
    steps: List[str] = []
    if site_raw is None:
        return "", "", steps
    site = str(site_raw).strip()
    if not site or site.lower() in {"n/a", "na"}:
        return site, "", steps

    steps.append("site_trim")
    normalized = site.lower().replace("-", " ")
    normalized = re.sub(r"\\s+", " ", normalized).strip()
    mapping = {
        "blr campus": "BLR CAMPUS",
        "blr": "BLR CAMPUS",
        "hq bldg 1": "HQ BLDG 1",
        "hq building 1": "HQ BLDG 1",
        "hq": "HQ",
        "lab 1": "LAB 1",
        "lab-1": "LAB 1",
        "dc 1": "DC 1",
    }
    site_norm = mapping.get(normalized, normalized.upper())
    steps.append("site_normalize")
    return site, site_norm, steps


def recommendations_for(issues: List[Dict]) -> List[str]:
    actions = {
        "ip": "Correct IP or mark record for review",
        "hostname": "Adjust hostname to RFC-compliant label",
        "fqdn": "Provide valid FQDN or clear the field",
        "mac": "Fix MAC address to 12 hex digits",
        "device_type": "Confirm device type",
    }
    recs = []
    for issue in issues:
        field = issue.get("field")
        if field in actions:
            recs.append(actions[field])
    return uniq(recs)


def process(input_csv: Path, out_csv: Path, anomalies_json: Path):
    anomalies: List[Dict] = []
    with input_csv.open() as f_in, out_csv.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in reader:
            row_steps: List[str] = []
            row_issues: List[Dict] = []

            ip_out, ip_valid, ip_version, subnet, ip_steps, ip_issues = normalize_ip(row.get("ip"))
            row_steps.extend(ip_steps)
            row_issues.extend(ip_issues)

            hostname, hostname_valid, fqdn, fqdn_consistent, name_steps, name_issues = normalize_names(
                row.get("hostname"), row.get("fqdn")
            )
            row_steps.extend(name_steps)
            row_issues.extend(name_issues)

            reverse_ptr = ""
            if ip_valid == "true":
                try:
                    reverse_ptr = ipaddress.ip_address(ip_out).reverse_pointer
                    row_steps.append("reverse_ptr_build")
                except ValueError:
                    reverse_ptr = ""

            mac_out, mac_valid, mac_steps, mac_issues = normalize_mac(row.get("mac"))
            row_steps.extend(mac_steps)
            row_issues.extend(mac_issues)

            owner, owner_email, owner_team, owner_steps = parse_owner(row.get("owner"))
            row_steps.extend(owner_steps)

            device_type, device_confidence, device_steps = normalize_device_type(
                row.get("device_type"), hostname, row.get("notes", "")
            )
            row_steps.extend(device_steps)

            site_raw, site_norm, site_steps = normalize_site(row.get("site"))
            row_steps.extend(site_steps)

            if row_issues:
                anomalies.append(
                    {
                        "source_row_id": row.get("source_row_id"),
                        "issues": row_issues,
                        "recommended_actions": recommendations_for(row_issues),
                    }
                )

            record = CleanRecord(
                ip=ip_out,
                ip_valid=ip_valid,
                ip_version=ip_version,
                subnet_cidr=subnet,
                hostname=hostname,
                hostname_valid=hostname_valid,
                fqdn=fqdn,
                fqdn_consistent=fqdn_consistent,
                reverse_ptr=reverse_ptr,
                mac=mac_out,
                mac_valid=mac_valid,
                owner=owner,
                owner_email=owner_email,
                owner_team=owner_team,
                device_type=device_type,
                device_type_confidence=device_confidence,
                site=site_raw.strip() if site_raw else "",
                site_normalized=site_norm,
                source_row_id=row.get("source_row_id"),
                normalization_steps="|".join(uniq(row_steps)),
            )
            writer.writerow(asdict(record))

    with anomalies_json.open("w") as f_anom:
        json.dump(anomalies, f_anom, indent=2)


def main():
    base = Path(__file__).parent
    output_dir = base / "deliverables"
    output_dir.mkdir(exist_ok=True)

    input_csv = Path("inventory_raw.csv")
    out_csv = output_dir / "inventory_clean.csv"
    anomalies_json = output_dir / "anomalies.json"
    process(input_csv, out_csv, anomalies_json)
    print(f"Wrote {out_csv} and {anomalies_json}")


if __name__ == "__main__":
    main()
