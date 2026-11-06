"""DLP-020 monitoring fixtures: Loki→Zabbix sync log, DQ state, automation state, AWX revisions.

The real hmdl-api (Datalake-Platform-GUI ``services/hmdl-api``, origin/development e9f39020)
reads ``hmdl.zabbix_sync_log`` / ``hmdl_datalake_dq_*`` and AWX. Here the same pure functions
run over generated rows, so every count, section and ``status_since`` agrees with the rows,
the way the real service derives them. Ported functions keep their GUI names; the source
file is named above each block. Severity does not exist anywhere in this API (spec v3).

Times are relative to an anchor (now, floored to 30 minutes) and rebuilt when it moves:
run ids stay stable inside a 30-minute window, and the newest sync run is always partly
running (virtual_fw) while device and platform are finished. Host names are generic
(``dc13-srv-001``); no customer or person names.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timedelta, timezone
from statistics import median

# GUI settings defaults (services/hmdl-api/app/config.py)
SYNC_SNAPSHOT_MIN = 10.0
SYNC_SETTLE_MIN = 45.0
SYNC_COMPLETE_RATIO = 0.9
GITHUB_REPO = "Duosis-Developer-Team/project-zabake"

# ── shared/hmdl/sync_reason.py ───────────────────────────────────────────────
STATUSES = ("eklendi", "güncellendi", "güncel", "eklenemedi", "güncellenemedi", "atlandı", "dry_run")
PROBLEM_STATUSES = frozenset({"eklenemedi", "güncellenemedi"})
_OK_STATUSES = frozenset({"eklendi", "güncellendi", "güncel"})
_RULES: tuple[tuple[str, re.Pattern], ...] = (
    ("ip_missing", re.compile(r"IP adresi bulunamadı", re.I)),
    ("vfw_location_missing", re.compile(r"Location \(lokasyon\) is missing on virtual firewall", re.I)),
    ("vfw_vendor_missing", re.compile(r"Vendor is missing on virtual firewall", re.I)),
    ("no_platform_mapping", re.compile(r"No platform mapping found for manufacturer", re.I)),
    ("no_vfw_mapping", re.compile(r"No virtual_fw mapping", re.I)),
    ("nonstandard_site_code", re.compile(r"Standart dışı site kodu", re.I)),
    ("template_missing", re.compile(r"Zabbix'te bulunamayan şablonlar|Template bulunamadı", re.I)),
    ("no_template_for_device_type", re.compile(r"No templates found for device_type", re.I)),
    ("device_type_not_found", re.compile(r"Device type bulunamadı", re.I)),
    ("proxy_group_missing", re.compile(r"Proxy group bulunamadı", re.I)),
    ("duplicate_host", re.compile(r"Host with the same name .* already exists", re.I)),
    ("zabbix_api_error", re.compile(r"Application error|Invalid params", re.I)),
)
_TR_UPPER = str.maketrans({"İ": "i", "I": "ı"})


def normalize_status(raw: str | None) -> str:
    s = (raw or "").strip().translate(_TR_UPPER).casefold()
    return s if s in STATUSES else "unknown"


def reason_code(status: str | None, reason: str | None) -> str:
    st = normalize_status(status)
    if st in _OK_STATUSES:
        return "none"
    text = reason or ""
    if st == "atlandı" and re.search(r"izlenmeyecek", text.translate(_TR_UPPER), re.I):
        return "not_monitored"
    for code, pattern in _RULES:
        if pattern.search(text):
            return code
    return "other_error" if st in PROBLEM_STATUSES else "none"


# ── shared/hmdl/entity_type.py ───────────────────────────────────────────────
_ROLE_TYPES = {"PLATFORM": "platform", "VIRTUAL_FW": "virtual_fw"}


def resolve_entity_type(host_entity_type: str | None, device_role: str | None) -> str:
    if (host_entity_type or "").strip(" \t\r\n"):
        return host_entity_type
    role = "".join(c.upper() if c.isascii() else c for c in (device_role or "").strip(" \t\r\n"))
    if not role:
        return "unknown"
    return _ROLE_TYPES.get(role, "device")


# ── app/services/dc_code.py ──────────────────────────────────────────────────
_DC_CODE_RE = re.compile(r"(DC|AZ|ICT|UZ)\d+", re.IGNORECASE)


def extract_dc_code(text: str | None) -> str:
    m = _DC_CODE_RE.search(str(text or ""))
    return m.group(0).upper() if m else ""


# ── app/services/zabbix_sync_runs.py ────────────────────────────────────────
SUMMARY_KEYS = ("eklendi", "güncellendi", "güncel", "eklenemedi", "güncellenemedi", "atlandı",
                "dry_run_create", "dry_run_update")
_SECTION_OF = {"eklenemedi": "failed", "güncellenemedi": "update_failed", "atlandı": "skipped",
               "eklendi": "added", "güncellendi": "updated"}
_SECTIONS = ("failed", "update_failed", "skipped", "added", "updated", "dry_run_create", "dry_run_update")


def iso(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(v)


def host_key(entity_type: str | None, device_id, name: str | None) -> str:
    et = entity_type or "unknown"
    if device_id not in (None, ""):
        return f"{et}:{device_id}"
    return f"{et}:name:{name or ''}"


def classify_runs(groups: list[dict], now: datetime, settle_min: float, ratio: float) -> list[dict]:
    settle = timedelta(minutes=settle_min)
    ordered = sorted(groups, key=lambda g: g["last_row_at"])
    out = []
    for g in ordered:
        finished = now - g["last_row_at"] >= settle
        refs = [h["row_count"] for h in ordered
                if h["entity_type"] == g["entity_type"] and not h["dry_run"] and h is not g
                and h["last_row_at"] < g["last_row_at"] and now - h["last_row_at"] >= settle][-10:]
        cov = None if len(refs) < 3 else round(g["row_count"] / median(refs), 4)
        if not finished or g["dry_run"]:
            complete = False
        elif cov is None:
            complete = None
        else:
            complete = cov >= ratio
        out.append({**g, "state": "finished" if finished else "running", "coverage_ratio": cov, "complete": complete})
    return sorted(out, key=lambda g: g["last_row_at"], reverse=True)


def _as_dict(v) -> dict:
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v.strip():
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, dict) else {}
        except ValueError:
            return {}
    return {}


def parse_changes(reason: str | None, field_merge_actions) -> tuple[list[dict], list[dict], list[dict]]:
    fma = _as_dict(field_merge_actions)
    items = fma.get("update_reasons")
    if not isinstance(items, list):
        items = [p for p in (reason or "").split(";")]
    fields, tags = [], []
    for raw in items:
        item = str(raw).strip()
        if not item:
            continue
        m = re.match(r"^ip_changed:(.*?)->(.*)$", item)
        if m:
            fields.append({"field": "ip", "old": m.group(1) or None, "new": m.group(2) or None, "kind": "ip_changed"})
        elif item.startswith("tags:"):
            tags.extend({"key": k} for k in re.findall(r"'([^']+)'", item))
        elif item.endswith("_changed"):
            fields.append({"field": item[: -len("_changed")], "old": None, "new": None, "kind": item})
    preserved = [{"field": k, "reason": fma.get(f"{k}_reason")} for k, v in fma.items() if v == "preserved_manual"]
    return fields, tags, preserved


def host_row(r: dict) -> dict:
    status = normalize_status(r.get("status"))
    fields, tags, preserved = parse_changes(r.get("reason"), r.get("field_merge_actions"))
    fma = _as_dict(r.get("field_merge_actions"))
    reasons = fma.get("update_reasons") if isinstance(fma.get("update_reasons"), list) else \
        [p.strip() for p in (r.get("reason") or "").split(";") if p.strip()] if status == "güncellendi" else []
    name = r.get("source_device_name")
    return {
        "host_key": host_key(r.get("host_entity_type"), r.get("source_device_id"), name),
        "entity_type": r.get("host_entity_type") or "unknown",
        "entity_type_inferred": bool(r.get("entity_type_inferred")),
        "source_device_id": r.get("source_device_id"),
        "name": name,
        "device_type": r.get("device_type"),
        "device_role": r.get("device_role"),
        "manufacturer": r.get("manufacturer_name"),
        "dc_code": extract_dc_code(r.get("root_location_name")) or extract_dc_code(r.get("location_name"))
        or extract_dc_code(r.get("site_name")) or extract_dc_code(name) or None,
        "site": r.get("site_name"),
        "location": r.get("location_name"),
        "tenant": r.get("tenant_name"),
        "ownership": None,  # not in zabbix_sync_log; never made up
        "ip": r.get("zabbix_host_ip"),
        "zabbix_hostid": r.get("zabbix_hostid"),
        "zabbix_hostname": r.get("zabbix_hostname"),
        "status": status,
        "operation": r.get("operation"),
        "reason": r.get("reason") or None,
        "reason_code": reason_code(status, r.get("reason")),
        "update_reasons": reasons,
        "field_changes": fields,
        "tag_changes": tags,
        "preserved": preserved,
        "error_detail": r.get("error_payload"),
        "run_id": r.get("run_id"),
        "processed_at": iso(r.get("processed_at")),
    }


def build_sections(rows: list[dict]) -> dict:
    summary = {k: 0 for k in SUMMARY_KEYS}
    sections: dict[str, list] = {s: [] for s in _SECTIONS}
    for r in rows:
        h = host_row(r)
        st = h["status"]
        if st == "dry_run" or r.get("dry_run"):
            key = "dry_run_create" if (r.get("operation") or "") == "create" else "dry_run_update"
            summary[key] += 1
            sections[key].append(h)
            continue
        if st in summary:
            summary[st] += 1
        sec = _SECTION_OF.get(st)
        if sec:
            sections[sec].append(h)
    return {"summary": summary, "sections": sections}


def run_view(g: dict) -> dict:
    return {
        "run_id": g["run_id"], "entity_type": g["entity_type"], "started_at": iso(g["started_at"]),
        "last_row_at": iso(g["last_row_at"]), "state": g["state"], "complete": g["complete"],
        "coverage_ratio": g["coverage_ratio"], "dry_run": g["dry_run"], "row_count": g["row_count"],
        "counts": {k: int(g["counts"].get(k, 0)) for k in SUMMARY_KEYS},
    }


# ── app/services/zabbix_sync_snapshot.py ─────────────────────────────────────
def fold_streaks(rows: list[dict]) -> dict[str, dict]:
    state: dict[str, dict] = {}
    for r in sorted(rows, key=lambda x: x["processed_at"]):
        status = normalize_status(r.get("status"))
        if r.get("dry_run") or status == "dry_run":
            continue
        rc = reason_code(status, r.get("reason"))
        key = host_key(r.get("host_entity_type"), r.get("source_device_id"), r.get("source_device_name"))
        cur = state.get(key)
        same = cur is not None and cur["status"] == status and cur["reason_code"] == rc
        if not same:
            since, runs = r["processed_at"], 1
        elif cur["last_run_id"] == r.get("run_id"):
            since, runs = cur["status_since"], cur["runs_in_status"]
        else:
            since, runs = cur["status_since"], cur["runs_in_status"] + 1
        state[key] = {**host_row(r), "status_since": since, "runs_in_status": runs,
                      "last_seen_at": r["processed_at"], "last_run_id": r.get("run_id")}
    return state


# ── app/services/dq_state.py ─────────────────────────────────────────────────
DQ_LEAF_TYPES = frozenset({"vm", "ibm_lpar"})
DQ_PROBLEM_KOK = frozenset({"live_no_data", "stale", "missing", "unavailable"})
_DQ_FIELDS = ("entity_key", "family", "entity_type", "entity_name", "dc_code", "platform", "metric_source",
              "kok_neden", "kok_neden_aciklama", "last_seen_at", "is_customer")


def _dq_key(e: dict) -> str:
    return f"{e.get('family')}|{e.get('entity_type')}|{e.get('entity_key')}"


def dq_advance(prev: dict[str, dict], run_id: str, finished_at: datetime, entities: list[dict],
               complete: bool | None) -> dict[str, dict]:
    new = {k: dict(v) for k, v in prev.items()}
    seen = set()
    for e in entities:
        k = _dq_key(e)
        seen.add(k)
        cur = prev.get(k)
        if cur is not None and cur["kok_neden"] == e.get("kok_neden"):
            since = cur["status_since"]
            runs = cur["runs_in_status"] + (0 if cur["last_run_id"] == run_id else 1)
        else:
            since, runs = finished_at, 1
        flag = True if complete else (cur["seen_in_latest_complete_run"] if cur else None)
        new[k] = {**{f: e.get(f) for f in _DQ_FIELDS}, "status_since": since, "runs_in_status": runs,
                  "last_run_id": run_id, "seen_in_latest_complete_run": flag}
    if complete:
        for k in new:
            if k not in seen:
                new[k]["seen_in_latest_complete_run"] = False
    return new


def dq_entities_response(state: dict, run: dict | None, now: datetime, *, kok_neden: str | None = None,
                         entity_type: str | None = None, family: str | None = None, dc: str | None = None,
                         problems_only: bool = False, include_leaf: bool = False) -> dict:
    out = []
    for e in state.values():
        if not include_leaf and e["entity_type"] in DQ_LEAF_TYPES:
            continue
        if problems_only and e["kok_neden"] not in DQ_PROBLEM_KOK:
            continue
        if kok_neden and e["kok_neden"] != kok_neden:
            continue
        if entity_type and e["entity_type"] != entity_type:
            continue
        if family and e["family"] != family:
            continue
        if dc and (e.get("dc_code") or "").upper() != dc.upper():
            continue
        last = e.get("last_seen_at")
        age = None if last is None else round((now - last).total_seconds() / 3600.0, 2)
        out.append({**e, "last_seen_at": iso(last), "status_since": iso(e["status_since"]), "age_hours": age,
                    "future_timestamp": bool(age is not None and age < 0)})
    out.sort(key=lambda x: (x["family"] or "", x["entity_type"] or "", x["entity_key"] or ""))
    return {"status_since_basis": "since_service_start",
            "run": {k: iso(v) if isinstance(v, datetime) else v for k, v in (run or {}).items()},
            "total": len(out), "entities": out}


def dq_runs_view(runs: list[dict], now: datetime, limit: int) -> list[dict]:
    groups = [{"run_id": r["run_id"], "entity_type": "dq", "started_at": r["started_at"],
               "last_row_at": r["finished_at"], "row_count": int(r["entity_count"] or 0),
               "dry_run": False, "counts": {}, "status": r["status"]} for r in runs[:limit + 10]]
    cl = classify_runs(groups, now, 10, SYNC_COMPLETE_RATIO)
    return [{"run_id": g["run_id"], "started_at": iso(g["started_at"]), "finished_at": iso(g["last_row_at"]),
             "status": g["status"], "entity_count": g["row_count"], "coverage_ratio": g["coverage_ratio"],
             "complete": bool(g["complete"]) and g["status"] == "ok" if g["complete"] is not None else None}
            for g in cl[:limit]]


# ═══════════════════════════════════════════════════════════════════════════
# Generated data
# ═══════════════════════════════════════════════════════════════════════════
_WINDOW = timedelta(minutes=30)
_SYNC_RUNS = 6                       # every 8 hours: two days of history
_SYNC_EVERY = timedelta(hours=8)
# Within one playbook run: device, then platform, then virtual_fw (minutes from the run start).
_PHASE = {"device": (0, 40), "platform": (41, 47), "virtual_fw": (49, 82)}
_RUN0_START = timedelta(minutes=92)  # run 0 starts 92 min before the anchor: vfw ends 10 min before it
_DRY_RUN_RUN = 1                     # this run also has a dry-run part (device)
_THIN = {("device", 2): 3, ("virtual_fw", 0): 6}  # (type, run) -> fillers seen per 5 / per 10 (incomplete, running)

_DCS = ("DC11", "DC12", "DC13", "DC14", "DC15", "DC16", "DC17", "AZ11", "ICT11")
_MAKES = (("HPE", "ProLiant DL380 Gen10", "HOST"), ("Dell", "PowerEdge R750", "HOST"),
          ("Lenovo", "ThinkSystem SR650", "HOST"), ("Cisco", "Nexus 93180YC-EX", "SWITCH"))


def _spec(et, did, name, *, make=None, dtype=None, role=None, dc=None, location=None, ip=None, status="güncel",
          since=_SYNC_RUNS - 1, prior="güncel", reason=None, op=None, fma=None, error=None, until=0,
          raw_type=True, raw_status=None):
    """One host's history: ``status`` from run ``since`` to the newest, ``prior`` before (None = not yet
    in NetBox); not seen after run ``until``. ``raw_status`` is the log's own spelling."""
    return {"et": et, "id": did, "name": name, "make": make, "dtype": dtype, "role": role, "dc": dc,
            "location": location, "ip": ip, "status": status, "since": since, "prior": prior, "reason": reason,
            "op": op, "fma": fma, "error": error, "until": until, "raw_type": raw_type, "raw_status": raw_status}


_LISTED = (
    _spec("device", 15231, "dc14-esx-07", make="HPE", dtype="ProLiant DL380 Gen10", role="HOST", dc="DC14",
          location="DC14-SALON-2", status="eklenemedi", prior=None, op="create",
          reason="IP adresi bulunamadı (primary_ip4 boş)"),
    _spec("device", 15240, "dc13-core-sw-01", make="Cisco", dtype="Nexus 93180YC-EX", role="SWITCH", dc="DC13",
          location="DC13-SALON-1", ip="10.134.0.12", status="güncellendi", since=0, op="update",
          reason="ip_changed:10.134.0.11->10.134.0.12;tags:['Rack', 'Location']"),
    _spec("device", 15302, "dc13-srv-r14-09", make="Lenovo", dtype="ThinkSystem SR650", role="HOST", dc="DC13",
          location="DC13-SALON-3", ip="10.134.41.9", status="güncellenemedi", raw_status="GÜNCELLENEMEDİ",
          since=1, op="update", reason="Proxy group bulunamadı: DC13-PG-02"),
    _spec("device", 15311, "dc13-srv-r14-10", make="HPE", dtype="ProLiant DL360 Gen11", role="HOST", dc="DC13",
          location="DC13-SALON-3", ip="10.134.41.10", status="eklendi", since=0, prior=None, op="create"),
    _spec("device", 16012, "dc11-stor-02", make="Dell", dtype="PowerStore 1000T", role="STORAGE", dc="DC11",
          location="DC11-SALON-1", ip="10.6.20.12", status="atlandı", raw_status="ATLANDI", op="skip",
          reason="Cihaz izlenmeyecek olarak işaretli (monitoring=false)", raw_type=False),
    _spec("device", 17007, "dc12-fw-mgmt-01", make="Fortinet", dtype="FortiGate 600E", role="FIREWALL", dc="DC12",
          location="DC12-SALON-1", ip="10.35.1.1", until=3),
    _spec("device", None, "dc16-pdu-a3", make="APC", dtype="AP8941", role="PDU", dc="DC16", location="DC16-SALON-1",
          ip="10.60.30.13", status="eklenemedi", since=3, prior=None, op="create",
          reason="Zabbix'te bulunamayan şablonlar: APC PDU by SNMP"),
    _spec("platform", 31, "dc11-vcenter-01", make="VMware", dtype="vCenter Server", role="PLATFORM", dc="DC11",
          location="DC11-SALON-1", ip="10.6.2.10", status="güncellenemedi", since=2, op="update",
          reason="Application error. Invalid params.",
          error={"code": -32602, "message": "Invalid params.",
                 "data": "Invalid parameter \"/1/tags/2\": value must be unique."}),
    _spec("platform", 44, "dc15-prism-01", make="Nutanix", dtype="Prism Central", role="PLATFORM", dc="DC15",
          location="DC15-SALON-1", ip="10.40.2.20"),
    _spec("virtual_fw", 884, "vfw-dc13-0884", role="VIRTUAL_FW", dc="DC13", location="DC13-SALON-2",
          ip="10.134.90.84", status="eklenemedi", prior=None, op="create",
          reason="Vendor is missing on virtual firewall vfw-dc13-0884"),
    _spec("virtual_fw", 902, "vfw-dc14-0902", make="Fortinet", dtype="FortiGate-VM", role="VIRTUAL_FW", dc="DC14",
          location="DC14-SALON-2", ip="10.50.90.2", status="güncellendi", since=0, op="update",
          reason="description_changed",
          fma={"update_reasons": ["description_changed"], "zabbix_hostname": "preserved_manual",
               "zabbix_hostname_reason": "Zabbix'te elle verilmiş ad korunuyor"}),
    _spec("virtual_fw", 1021, "vfw-dc15-1021", make="Fortinet", dtype="FortiGate-VM", role="VIRTUAL_FW", dc="DC15",
          location="DC15-SALON-1", ip="10.40.90.21", status="eklendi", since=0, prior=None, op="create"),
    _spec("virtual_fw", 933, "vfw-ict11-0933", make="Fortinet", dtype="FortiGate-VM", role="VIRTUAL_FW",
          ip="10.70.90.33", status="eklenemedi", since=4, prior=None, op="create",
          reason="Location (lokasyon) is missing on virtual firewall vfw-ict11-0933"),
)


def _fillers() -> list[dict]:
    out = []
    for n in range(230):
        dc = _DCS[n % len(_DCS)]
        make, dtype, role = _MAKES[n % len(_MAKES)]
        kind = "sw" if role == "SWITCH" else "srv"
        out.append(_spec("device", 20001 + n, f"{dc.lower()}-{kind}-{n + 1:03d}", make=make, dtype=dtype, role=role,
                         dc=dc, location=f"{dc}-SALON-{1 + n % 3}", ip=f"10.{100 + n % 9}.{n // 200}.{n % 250 + 1}"))
    for n in range(18):
        dc = _DCS[n % len(_DCS)]
        make, dtype = (("VMware", "vCenter Server"), ("Nutanix", "Prism Element"))[n % 2]
        out.append(_spec("platform", 100 + n, f"{dc.lower()}-{'vcenter' if n % 2 == 0 else 'prism'}-{n // 9 + 2:02d}",
                         make=make, dtype=dtype, role="PLATFORM", dc=dc, location=f"{dc}-SALON-1",
                         ip=f"10.{100 + n % 9}.2.{20 + n}"))
    for n in range(52):
        dc = _DCS[n % len(_DCS)]
        out.append(_spec("virtual_fw", 1100 + n, f"vfw-{dc.lower()}-{1100 + n:04d}", make="Fortinet",
                         dtype="FortiGate-VM", role="VIRTUAL_FW", dc=dc, location=f"{dc}-SALON-{1 + n % 2}",
                         ip=f"10.{100 + n % 9}.90.{n + 1}"))
    return out


_DRY = (  # run _DRY_RUN_RUN, device: what a dry-run would create / update
    _spec("device", 17101, "dc17-srv-new-01", make="Dell", dtype="PowerEdge R760", role="HOST", dc="DC17",
          location="DC17-SALON-1", ip="10.90.41.1", status="dry_run", op="create", reason="dry-run: oluşturulacak"),
    _spec("device", 17102, "dc17-srv-new-02", make="Dell", dtype="PowerEdge R760", role="HOST", dc="DC17",
          location="DC17-SALON-1", ip="10.90.41.2", status="dry_run", op="create", reason="dry-run: oluşturulacak"),
    _spec("device", 15240, "dc13-core-sw-01", make="Cisco", dtype="Nexus 93180YC-EX", role="SWITCH", dc="DC13",
          location="DC13-SALON-1", ip="10.134.0.12", status="dry_run", op="update",
          reason="dry-run: ip_changed:10.134.0.11->10.134.0.12"),
)


def _raw_row(s: dict, run_id: str, at: datetime, status: str, *, dry: bool = False) -> dict:
    """A hmdl.zabbix_sync_log row as the sync writes it."""
    existing = status not in ("eklenemedi",) and not (dry and s["op"] == "create")
    current = status == s["status"]
    upper = {"güncel": "GÜNCEL", "eklendi": "EKLENDİ", "güncellendi": "GÜNCELLENDİ", "eklenemedi": "EKLENEMEDİ",
             "güncellenemedi": "GÜNCELLENEMEDİ", "atlandı": "ATLANDI", "dry_run": "DRY_RUN"}
    return {
        "run_id": run_id, "host_entity_type": s["et"] if s["raw_type"] else None,
        "source_device_id": s["id"], "source_device_name": s["name"],
        "status": (s["raw_status"] if current and s["raw_status"] else upper[status]),
        "operation": (s["op"] if current else "update"), "reason": (s["reason"] if current else None),
        "field_merge_actions": (s["fma"] if current else None), "error_payload": (s["error"] if current else None),
        "dry_run": dry, "device_type": s["dtype"], "device_role": s["role"], "manufacturer_name": s["make"],
        "site_name": s["dc"], "location_name": s["location"], "root_location_name": s["dc"], "tenant_name": None,
        "zabbix_host_ip": s["ip"], "zabbix_hostid": (str(40000 + (s["id"] or 7)) if existing else None),
        "zabbix_hostname": (s["name"] if existing else None), "processed_at": at,
    }


def _select(raw: dict) -> dict:
    """``_ROW_COLS``: the type is resolved from the role when the log has none."""
    et = resolve_entity_type(raw.get("host_entity_type"), raw.get("device_role"))
    return {**raw, "host_entity_type": et,
            "entity_type_inferred": not (raw.get("host_entity_type") or "").strip() and et != "unknown"}


def _sync_rows(anchor: datetime) -> list[dict]:
    rows = []
    listed, fillers = list(_LISTED), _fillers()
    for k in range(_SYNC_RUNS - 1, -1, -1):
        start = anchor - _RUN0_START - _SYNC_EVERY * k
        run_id = start.strftime("%Y%m%d%H%M%S")
        for et, (a, b) in _PHASE.items():
            mine = [s for s in listed if s["et"] == et]
            thin = _THIN.get((et, k))
            fill = [s for i, s in enumerate(f for f in fillers if f["et"] == et)
                    if thin is None or i % (5 if k == 2 else 10) < thin]
            hosts = mine + fill
            span = (b - a) * 60
            for i, s in enumerate(hosts):
                if k < s["until"]:
                    continue
                status = s["status"] if k <= s["since"] else s["prior"]
                if status is None:
                    continue
                at = start + timedelta(minutes=a, seconds=int(span * i / max(1, len(hosts) - 1)))
                rows.append(_raw_row(s, run_id, at, status))
            if et == "device" and k == _DRY_RUN_RUN:
                for i, s in enumerate(_DRY):
                    rows.append(_raw_row(s, run_id, start + timedelta(minutes=2, seconds=20 * i), "dry_run", dry=True))
    return [_select(r) for r in rows]


def _run_groups(rows: list[dict]) -> list[dict]:
    """``fetch_run_groups``: run_id × type × dry_run, with status counts."""
    acc: dict[tuple, dict] = {}
    for r in rows:
        key = (r["run_id"], r["host_entity_type"], bool(r["dry_run"]))
        g = acc.setdefault(key, {"run_id": r["run_id"], "entity_type": r["host_entity_type"],
                                 "started_at": r["processed_at"], "last_row_at": r["processed_at"], "row_count": 0,
                                 "dry_run": bool(r["dry_run"]), "counts": {}})
        g["started_at"] = min(g["started_at"], r["processed_at"])
        g["last_row_at"] = max(g["last_row_at"], r["processed_at"])
        g["row_count"] += 1
        st = normalize_status(r["status"])
        if st == "dry_run":
            st = "dry_run_create" if (r.get("operation") or "") == "create" else "dry_run_update"
        g["counts"][st] = g["counts"].get(st, 0) + 1
    return list(acc.values())


# ── DQ ──────────────────────────────────────────────────────────────────────
_DQ_EVERY = timedelta(hours=2)
_DQ_RUNS = 48
_DQ_SERVICE_RUNS = 12                # hmdl-api restarted a day ago: status_since counts from there
_DQ_THIN_RUN = 3                     # this run wrote fewer rows (partial)
_DQ_TOTAL = 6612


def _dq_spec(family, et, name, platform, source, kok, *, dc, since=0, aciklama=None, seen_h=1.0, customer=False):
    return {"family": family, "entity_type": et, "entity_name": name, "platform": platform, "metric_source": source,
            "kok_neden": kok, "dc_code": dc, "since": since, "aciklama": aciklama, "seen_h": seen_h,
            "is_customer": customer}


_DQ = (
    _dq_spec("virt", "cluster", "DC13-CL-VMW-PROD-01", "vmware", "cluster_metrics", "ok", dc="DC13", since=11),
    _dq_spec("virt", "cluster", "DC14-CL-NTX-02", "nutanix", "nutanix_cluster_metrics", "stale", dc="DC14", since=4,
             aciklama="Son veri 30 saat önce; eşik 26 saat", seen_h=30.0),
    _dq_spec("virt", "cluster", "UZ11-CL-VMW-01", "vmware", "cluster_metrics", "ok", dc="UZ11", since=11,
             seen_h=-2.5),  # naive local time read as UTC: three hours ahead (datalake mixed time zones)
    _dq_spec("virt", "host", "dc11-esx-r03-12", "vmware", "host_metrics", "live_no_data", dc="DC11", since=7,
             aciklama="Canlı envanterde var, metrik gelmiyor", seen_h=None),
    _dq_spec("virt", "ibm_host", "DC16-P10-E1080-01", "ibm", "ibm_host_general", "missing", dc="DC16", since=2,
             aciklama="Envanterde var, datalake'te hiç satırı yok", seen_h=None),
    _dq_spec("backup", "veeam_endpoint", "dc13-veeam-01", "veeam", "raw_veeam_sessions", "unavailable", dc="DC13",
             since=1, aciklama="Kaynak API'ye erişilemedi", seen_h=7.5),
    _dq_spec("backup", "netbackup_source", "dc15-nbu-master", "netbackup", "raw_netbackup_jobs_metrics", "ok",
             dc="DC15", since=11, seen_h=2.0),
    _dq_spec("backup", "zerto_site", "DC12-ZERTO", "zerto", "raw_zerto_site_metrics", "stale", dc="DC12", since=0,
             aciklama="Son veri 27 saat önce; eşik 26 saat", seen_h=27.0),
    _dq_spec("storage", "storage", "dc13-pstore-01", "powerstore", "storage_capacity", "ok", dc="DC13", since=11,
             seen_h=0.5),
    _dq_spec("virt", "vm", "vm-dc13-0142", "vmware", "vm_metrics", "live_no_data", dc="DC13", since=5,
             aciklama="VM açık, metrik gelmiyor", seen_h=None, customer=True),
    _dq_spec("virt", "vm", "vm-dc14-0877", "nutanix", "vm_metrics", "ok", dc="DC14", since=11, customer=True),
    _dq_spec("virt", "ibm_lpar", "lpar-dc16-0031", "ibm", "ibm_lpar_general", "stale", dc="DC16", since=3,
             aciklama="Son veri 52 saat önce; eşik 26 saat", seen_h=52.0, customer=True),
)


def _dq_entity(s: dict, kok: str, anchor: datetime) -> dict:
    """A ``hmdl_datalake_dq_entity`` row; before its problem began the entity was ``ok`` and seen an hour ago."""
    key = s["entity_name"] if s["entity_type"] != "cluster" else f"{s['entity_name']}|{s['metric_source']}"
    if kok == s["kok_neden"]:
        seen = None if s["seen_h"] is None else anchor - timedelta(hours=s["seen_h"])
    else:
        seen = anchor - timedelta(hours=1)
    return {"entity_key": key, "family": s["family"], "entity_type": s["entity_type"],
            "entity_name": s["entity_name"], "dc_code": s["dc_code"], "platform": s["platform"],
            "metric_source": s["metric_source"], "kok_neden": kok,
            "kok_neden_aciklama": s["aciklama"] if kok == s["kok_neden"] else None,
            "last_seen_at": seen, "is_customer": s["is_customer"]}


# ── automations (AUTOMATION_SPECS order and thresholds) ─────────────────────
_AUTOMATIONS = (
    ("zabbix_sync", "NetBox → Zabbix Sync", "~8 saatte bir", 12.0, 24.0),
    ("collector_sync", "Datalake Collector Sync", "günlük 02:00", 26.0, 50.0),
    ("reachability_checks", "Collector Reachability Checks", "collector sync ile", 26.0, 50.0),
    ("vm_reconciliation", "VM Envanter Reconciliation", "günlük", 48.0, 120.0),
)

# ── AWX (project 18 "HMDL"; the GitHub compare answer per revision) ──────────
_AWX_JOBS = (
    (26, "netbox-zabbix-integration", "successful", "486b9e2c41f07a5d93e1b6c08d2f4a7e15c9b3d0", "behind"),
    (52, "hmdl-collector-sync", "successful", "486b9e2c41f07a5d93e1b6c08d2f4a7e15c9b3d0", "behind"),
    (55, "hmdl-reachability-checks", "failed", "9f3ab61d0c2e47b8a51f6d93e0b7c24a8d1e5f62", "ahead"),
    (63, "hmdl-vm-reconciliation", "successful", None, None),
    (64, "hmdl-loki-location-sync", "successful", "c03d5e7a9b1f24c68e0d3a57b2f9e41c6a8d0b13", None),
)


def _revision_report(jobs: list[dict], compare) -> list[dict]:
    """``awx_revisions.revision_report``."""
    seen: dict[str, str | None] = {}
    out = []
    for j in jobs:
        rev = (j.get("scm_revision") or "").strip()
        if not rev:
            out.append({**j, "on_main": None, "reason": "revizyon yok"})
            continue
        if rev not in seen:
            seen[rev] = compare(rev)
        status = seen[rev]
        if status in ("identical", "behind"):
            on_main, reason = True, None
        elif status in ("ahead", "diverged"):
            on_main, reason = False, f"main dışı kod (github: {status})"
        else:
            on_main, reason = None, "github karşılaştırması yapılamadı"
        out.append({**j, "on_main": on_main, "reason": reason})
    return out


# ═══════════════════════════════════════════════════════════════════════════
def _build(anchor: datetime) -> dict:
    rows = _sync_rows(anchor)
    groups = classify_runs(_run_groups(rows), anchor, SYNC_SETTLE_MIN, SYNC_COMPLETE_RATIO)
    hosts = fold_streaks(rows)
    latest_complete: dict[str, str] = {}
    for g in groups:
        if g["complete"] and g["entity_type"] not in latest_complete:
            latest_complete[g["entity_type"]] = g["run_id"]
    keys_by_type: dict[str, set] = {et: set() for et in latest_complete}
    for r in rows:
        if not r["dry_run"] and latest_complete.get(r["host_entity_type"]) == r["run_id"]:
            keys_by_type[r["host_entity_type"]].add(
                host_key(r["host_entity_type"], r["source_device_id"], r["source_device_name"]))
    for key, h in hosts.items():
        keys = keys_by_type.get(h["entity_type"])
        h["seen_in_latest_complete_run"] = None if keys is None else key in keys
    resolution = {"inferred_rows": sum(1 for r in rows if r["entity_type_inferred"]),
                  "unresolved_rows": sum(1 for r in rows if r["host_entity_type"] == "unknown"),
                  "role_conflicts": 0}

    # DQ: 48 runs every two hours; state advanced over the last 12 (since the service started).
    dq_runs = []
    for i in range(_DQ_RUNS):
        fin = anchor - timedelta(minutes=20) - _DQ_EVERY * i
        count = _DQ_TOTAL - 7 * (i % 4) if i != _DQ_THIN_RUN else 3120
        dq_runs.append({"run_id": f"dq-{fin:%Y%m%dT%H%M%S}", "started_at": fin - timedelta(minutes=41),
                        "finished_at": fin, "status": "ok", "entity_count": count})
    dq_view = dq_runs_view(dq_runs, anchor, _DQ_SERVICE_RUNS)
    state: dict[str, dict] = {}
    for i in range(_DQ_SERVICE_RUNS - 1, -1, -1):
        run = dq_view[i]
        ents = [_dq_entity(s, s["kok_neden"] if i <= s["since"] else "ok", anchor) for s in _DQ
                if not (i == _DQ_THIN_RUN and s["entity_type"] in DQ_LEAF_TYPES)]
        state = dq_advance(state, run["run_id"], dq_runs[i]["finished_at"], ents, run["complete"])

    # Automations: the zabbix sync's last non-dry row, the collector sync at 02:00 UTC.
    last_sync = max(r["processed_at"] for r in rows if not r["dry_run"])
    collector = anchor.replace(hour=2, minute=38, second=0)
    if collector > anchor:
        collector -= timedelta(days=1)
    last = {"zabbix_sync": last_sync, "collector_sync": collector,
            "reachability_checks": anchor - timedelta(hours=31, minutes=12),
            "vm_reconciliation": anchor - timedelta(hours=130)}
    service_start = anchor - timedelta(hours=24)
    autos = []
    for key, label, cadence, warn, dead in _AUTOMATIONS:
        age = round((anchor - last[key]).total_seconds() / 3600.0, 4)
        st = "dead" if age >= dead else "stale" if age >= warn else "fresh"
        since = service_start if st != "stale" else last[key] + timedelta(hours=warn)
        autos.append({"key": key, "label": label, "cadence": cadence, "last_run_at": last[key].isoformat(),
                      "age_hours": age, "warn_hours": warn, "dead_hours": dead, "state": st,
                      "status_since": iso(max(since, service_start))})

    compare = {rev: answer for _, _, _, rev, answer in _AWX_JOBS if rev}
    jobs = [{"job_template": jt, "job_template_name": name, "project": 18, "project_name": "HMDL",
             "branch": "development", "last_job_id": 110400 + n * 37,
             "last_job_finished": (anchor - timedelta(hours=1 + n * 3, minutes=17)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
             "last_job_status": status, "scm_revision": rev}
            for n, (jt, name, status, rev, _) in enumerate(_AWX_JOBS)]
    report = _revision_report(jobs, compare.get)

    return {"anchor": anchor, "rows": rows, "groups": groups, "hosts": hosts, "resolution": resolution,
            "dq_runs": dq_runs, "dq_state": state, "dq_run": dq_view[0], "automations": autos,
            "service_start": service_start,
            "awx": {"repo": GITHUB_REPO, "jobs": report,
                    "off_main": sum(1 for j in report if j["on_main"] is False),
                    "unknown": sum(1 for j in report if j["on_main"] is None)}}


_lock = threading.Lock()
_cache: dict | None = None


def anchor_for(now: datetime) -> datetime:
    floor = now.replace(minute=(now.minute // 30) * 30, second=0, microsecond=0)
    return floor


def state(now: datetime | None = None) -> dict:
    """The fixtures for the current 30-minute window (rebuilt when the window moves)."""
    global _cache
    anchor = anchor_for(now or datetime.now(timezone.utc))
    with _lock:
        if _cache is None or _cache["anchor"] != anchor:
            _cache = _build(anchor)
        return _cache
