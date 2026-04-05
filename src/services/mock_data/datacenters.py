"""Mock datacenter summaries, DC detail payloads, SLA map, and global dashboard aggregates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

MOCK_DC_CODES: tuple[str, ...] = ("IST-DC1", "ANK-DC1", "IZM-DC1", "FRA-DC1")


def _norm_dc(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


def _arch_usage(cpu_c: float, ram_c: float, disk_c: float) -> dict[str, Any]:
    return {
        "classic": {"cpu_pct": cpu_c, "ram_pct": ram_c, "disk_pct": disk_c},
        "hyperconv": {"cpu_pct": cpu_c * 0.95, "ram_pct": ram_c * 0.92, "disk_pct": disk_c * 0.88},
        "ibm": {"cpu_pct": cpu_c * 0.9, "ram_pct": ram_c * 0.9, "disk_pct": disk_c * 0.85},
    }


def _summary_row(
    dc_id: str,
    name: str,
    location: str,
    description: str,
    *,
    platforms: int,
    clusters: int,
    hosts: int,
    vms: int,
    cpu_pct: float,
    ram_pct: float,
    stor_pct: float,
    energy_kw: float,
    ibm_kw: float,
    vcenter_kw: float,
) -> dict[str, Any]:
    return {
        "id": dc_id,
        "name": name,
        "location": location,
        "description": description,
        "site_name": dc_id.split("-")[0],
        "status": "Operational",
        "platform_count": platforms,
        "cluster_count": clusters,
        "host_count": hosts,
        "vm_count": vms,
        "stats": {
            "total_cpu": f"{hosts * 32} vCPU",
            "used_cpu_pct": cpu_pct,
            "total_ram": f"{hosts * 512} GB",
            "used_ram_pct": ram_pct,
            "total_storage": f"{hosts * 24} TB",
            "used_storage_pct": stor_pct,
            "last_updated": "mock",
            "total_energy_kw": energy_kw,
            "ibm_kw": ibm_kw,
            "vcenter_kw": vcenter_kw,
            "arch_usage": _arch_usage(cpu_pct, ram_pct, stor_pct),
        },
    }


_MOCK_SUMMARIES: list[dict[str, Any]] = [
    _summary_row(
        "IST-DC1",
        "Istanbul DC 1",
        "Istanbul, TR",
        "Primary metro — Classic (KM), Hyperconverged, Power",
        platforms=3,
        clusters=6,
        hosts=46,
        vms=1050,
        cpu_pct=72.0,
        ram_pct=68.0,
        stor_pct=61.0,
        energy_kw=420.0,
        ibm_kw=95.0,
        vcenter_kw=325.0,
    ),
    _summary_row(
        "ANK-DC1",
        "Ankara DC 1",
        "Ankara, TR",
        "Central region — Classic (KM) + Power",
        platforms=2,
        clusters=4,
        hosts=28,
        vms=420,
        cpu_pct=45.0,
        ram_pct=51.0,
        stor_pct=78.0,
        energy_kw=210.0,
        ibm_kw=120.0,
        vcenter_kw=90.0,
    ),
    _summary_row(
        "IZM-DC1",
        "Izmir DC 1",
        "Izmir, TR",
        "Coastal edge — Hyperconverged footprint",
        platforms=1,
        clusters=3,
        hosts=18,
        vms=520,
        cpu_pct=83.0,
        ram_pct=79.0,
        stor_pct=55.0,
        energy_kw=180.0,
        ibm_kw=0.0,
        vcenter_kw=180.0,
    ),
    _summary_row(
        "FRA-DC1",
        "Frankfurt DC 1",
        "Frankfurt, DE",
        "EU region — Classic (KM) + Hyperconverged (DR target for IST)",
        platforms=2,
        clusters=5,
        hosts=32,
        vms=680,
        cpu_pct=38.0,
        ram_pct=42.0,
        stor_pct=47.0,
        energy_kw=265.0,
        ibm_kw=0.0,
        vcenter_kw=265.0,
    ),
]


def _compute_block(
    *,
    hosts: int,
    vms: int,
    cpu_cap: float,
    cpu_used: float,
    mem_cap: float,
    mem_used: float,
    stor_cap_tb: float,
    stor_used_tb: float,
    cpu_pct_max: float = 0.0,
    mem_pct_max: float = 0.0,
) -> dict[str, Any]:
    return {
        "hosts": hosts,
        "vms": vms,
        "cpu_cap": cpu_cap,
        "cpu_used": cpu_used,
        "mem_cap": mem_cap,
        "mem_used": mem_used,
        "stor_cap": stor_cap_tb,
        "stor_used": stor_used_tb,
        "cpu_pct_max": cpu_pct_max,
        "mem_pct_max": mem_pct_max,
    }


def _power_block(
    *,
    hosts: int,
    vios: int,
    lpars: int,
    cpu_used: float,
    cpu_assigned: float,
    mem_total: float,
    mem_assigned: float,
    storage_cap_tb: float = 0.0,
    storage_used_tb: float = 0.0,
    stor_used_tb: float | None = None,
) -> dict[str, Any]:
    return {
        "hosts": hosts,
        "vms": lpars,
        "vios": vios,
        "lpar_count": lpars,
        "cpu": int(cpu_assigned),
        "cpu_used": cpu_used,
        "cpu_assigned": cpu_assigned,
        "ram": int(mem_total),
        "memory_total": mem_total,
        "memory_assigned": mem_assigned,
        "storage_cap_tb": storage_cap_tb,
        "storage_used_tb": stor_used_tb if stor_used_tb is not None else storage_used_tb,
    }


_MOCK_DC_DETAILS: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "meta": {
            "name": "Istanbul DC 1",
            "location": "Istanbul, TR",
            "description": "Primary metro — Classic (KM), Hyperconverged, Power",
        },
        "intel": {
            "clusters": 6,
            "hosts": 46,
            "vms": 1050,
            "cpu_cap": 1472.0,
            "cpu_used": 1060.0,
            "ram_cap": 23552.0,
            "ram_used": 16000.0,
            "storage_cap": 920.0,
            "storage_used": 561.0,
        },
        "classic": _compute_block(
            hosts=12,
            vms=340,
            cpu_cap=384.0,
            cpu_used=277.0,
            mem_cap=6144.0,
            mem_used=4200.0,
            stor_cap_tb=320.0,
            stor_used_tb=195.0,
            cpu_pct_max=88.0,
            mem_pct_max=82.0,
        ),
        "hyperconv": _compute_block(
            hosts=8,
            vms=190,
            cpu_cap=256.0,
            cpu_used=195.0,
            mem_cap=4096.0,
            mem_used=3100.0,
            stor_cap_tb=180.0,
            stor_used_tb=98.0,
            cpu_pct_max=91.0,
            mem_pct_max=85.0,
        ),
        "power": _power_block(
            hosts=4,
            vios=2,
            lpars=8,
            cpu_used=420.0,
            cpu_assigned=512.0,
            mem_total=8192.0,
            mem_assigned=6100.0,
            storage_cap_tb=120.0,
            storage_used_tb=72.0,
        ),
        "energy": {
            "total_kw": 420.0,
            "ibm_kw": 95.0,
            "vcenter_kw": 325.0,
            "total_kwh": 10080.0,
            "ibm_kwh": 2280.0,
            "vcenter_kwh": 7800.0,
        },
        "platforms": {"nutanix": {"hosts": 8, "vms": 190}, "vmware": {"clusters": 3, "hosts": 12, "vms": 340}, "ibm": {"hosts": 4, "vios": 2, "lpars": 8}},
    },
    "ANK-DC1": {
        "meta": {
            "name": "Ankara DC 1",
            "location": "Ankara, TR",
            "description": "Central region — Classic (KM) + Power",
        },
        "intel": {
            "clusters": 4,
            "hosts": 28,
            "vms": 420,
            "cpu_cap": 896.0,
            "cpu_used": 403.0,
            "ram_cap": 14336.0,
            "ram_used": 7310.0,
            "storage_cap": 560.0,
            "storage_used": 437.0,
        },
        "classic": _compute_block(
            hosts=8,
            vms=210,
            cpu_cap=256.0,
            cpu_used=115.0,
            mem_cap=4096.0,
            mem_used=2090.0,
            stor_cap_tb=400.0,
            stor_used_tb=312.0,
            cpu_pct_max=62.0,
            mem_pct_max=58.0,
        ),
        "hyperconv": {},
        "power": _power_block(
            hosts=6,
            vios=2,
            lpars=12,
            cpu_used=310.0,
            cpu_assigned=400.0,
            mem_total=10240.0,
            mem_assigned=5220.0,
            storage_cap_tb=160.0,
            stor_used_tb=125.0,
        ),
        "energy": {
            "total_kw": 210.0,
            "ibm_kw": 120.0,
            "vcenter_kw": 90.0,
            "total_kwh": 5040.0,
            "ibm_kwh": 2880.0,
            "vcenter_kwh": 2160.0,
        },
        "platforms": {"nutanix": {"hosts": 0, "vms": 0}, "vmware": {"clusters": 2, "hosts": 8, "vms": 210}, "ibm": {"hosts": 6, "vios": 2, "lpars": 12}},
    },
    "IZM-DC1": {
        "meta": {
            "name": "Izmir DC 1",
            "location": "Izmir, TR",
            "description": "Hyperconverged — capacity pressure scenario",
        },
        "intel": {
            "clusters": 3,
            "hosts": 18,
            "vms": 520,
            "cpu_cap": 576.0,
            "cpu_used": 478.0,
            "ram_cap": 9216.0,
            "ram_used": 7280.0,
            "storage_cap": 360.0,
            "storage_used": 198.0,
        },
        "classic": {},
        "hyperconv": _compute_block(
            hosts=18,
            vms=520,
            cpu_cap=576.0,
            cpu_used=478.0,
            mem_cap=9216.0,
            mem_used=7280.0,
            stor_cap_tb=360.0,
            stor_used_tb=198.0,
            cpu_pct_max=94.0,
            mem_pct_max=89.0,
        ),
        "power": {},
        "energy": {
            "total_kw": 180.0,
            "ibm_kw": 0.0,
            "vcenter_kw": 180.0,
            "total_kwh": 4320.0,
            "ibm_kwh": 0.0,
            "vcenter_kwh": 4320.0,
        },
        "platforms": {"nutanix": {"hosts": 18, "vms": 520}, "vmware": {"clusters": 0, "hosts": 0, "vms": 0}, "ibm": {"hosts": 0, "vios": 0, "lpars": 0}},
    },
    "FRA-DC1": {
        "meta": {
            "name": "Frankfurt DC 1",
            "location": "Frankfurt, DE",
            "description": "EU Classic (KM) + Hyperconverged — healthy headroom",
        },
        "intel": {
            "clusters": 5,
            "hosts": 32,
            "vms": 680,
            "cpu_cap": 1024.0,
            "cpu_used": 389.0,
            "ram_cap": 16384.0,
            "ram_used": 6880.0,
            "storage_cap": 640.0,
            "storage_used": 301.0,
        },
        "classic": _compute_block(
            hosts=10,
            vms=280,
            cpu_cap=320.0,
            cpu_used=122.0,
            mem_cap=5120.0,
            mem_used=2150.0,
            stor_cap_tb=400.0,
            stor_used_tb=188.0,
            cpu_pct_max=48.0,
            mem_pct_max=44.0,
        ),
        "hyperconv": _compute_block(
            hosts=6,
            vms=140,
            cpu_cap=192.0,
            cpu_used=73.0,
            mem_cap=3072.0,
            mem_used=1290.0,
            stor_cap_tb=240.0,
            stor_used_tb=113.0,
            cpu_pct_max=42.0,
            mem_pct_max=40.0,
        ),
        "power": {},
        "energy": {
            "total_kw": 265.0,
            "ibm_kw": 0.0,
            "vcenter_kw": 265.0,
            "total_kwh": 6360.0,
            "ibm_kwh": 0.0,
            "vcenter_kwh": 6360.0,
        },
        "platforms": {"nutanix": {"hosts": 6, "vms": 140}, "vmware": {"clusters": 2, "hosts": 10, "vms": 280}, "ibm": {"hosts": 0, "vios": 0, "lpars": 0}},
    },
}


def get_all_datacenters_summary(_tr: dict | None = None) -> list[dict[str, Any]]:
    return deepcopy(_MOCK_SUMMARIES)


def get_dc_detail(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    key = _norm_dc(dc_code)
    base = _MOCK_DC_DETAILS.get(key)
    if not base:
        empty = {
            "meta": {"name": dc_code, "location": "", "description": ""},
            "intel": {},
            "classic": {},
            "hyperconv": {},
            "power": {},
            "energy": {},
            "platforms": {},
        }
        return deepcopy(empty)
    return deepcopy(base)


def get_sla_by_dc_payload(_tr: dict | None = None) -> dict[str, dict[str, Any]]:
    """Keyed by uppercase DC code."""
    return {
        "IST-DC1": {
            "availability_pct": 99.982,
            "period_hours": 168.0,
            "downtime_hours": 0.03,
        },
        "ANK-DC1": {
            "availability_pct": 99.91,
            "period_hours": 168.0,
            "downtime_hours": 0.15,
        },
        "IZM-DC1": {
            "availability_pct": 99.85,
            "period_hours": 168.0,
            "downtime_hours": 0.25,
        },
        "FRA-DC1": {
            "availability_pct": 99.995,
            "period_hours": 168.0,
            "downtime_hours": 0.01,
        },
    }


def build_global_dashboard(_tr: dict | None = None) -> dict[str, Any]:
    summaries = _MOCK_SUMMARIES
    total_hosts = sum(s["host_count"] for s in summaries)
    total_vms = sum(s["vm_count"] for s in summaries)
    plat = sum(s["platform_count"] for s in summaries)
    energy_ibm = sum(s["stats"]["ibm_kw"] for s in summaries)
    energy_vc = sum(s["stats"]["vcenter_kw"] for s in summaries)

    def _sum_classic_hyperconv():
        c_cpu = c_ram = c_st = 0.0
        h_cpu = h_ram = h_st = 0.0
        for code in MOCK_DC_CODES:
            d = _MOCK_DC_DETAILS[code]
            cl = d.get("classic") or {}
            hy = d.get("hyperconv") or {}
            c_cpu += float(cl.get("cpu_cap", 0) or 0)
            c_ram += float(cl.get("mem_cap", 0) or 0)
            c_st += float(cl.get("stor_cap", 0) or 0)
            h_cpu += float(hy.get("cpu_cap", 0) or 0)
            h_ram += float(hy.get("mem_cap", 0) or 0)
            h_st += float(hy.get("stor_cap", 0) or 0)
        return (c_cpu, sum(float(_MOCK_DC_DETAILS[c].get("classic", {}).get("cpu_used", 0) or 0) for c in MOCK_DC_CODES),
                c_ram, sum(float(_MOCK_DC_DETAILS[c].get("classic", {}).get("mem_used", 0) or 0) for c in MOCK_DC_CODES),
                c_st, sum(float(_MOCK_DC_DETAILS[c].get("classic", {}).get("stor_used", 0) or 0) for c in MOCK_DC_CODES),
                h_cpu, sum(float(_MOCK_DC_DETAILS[c].get("hyperconv", {}).get("cpu_used", 0) or 0) for c in MOCK_DC_CODES),
                h_ram, sum(float(_MOCK_DC_DETAILS[c].get("hyperconv", {}).get("mem_used", 0) or 0) for c in MOCK_DC_CODES),
                h_st, sum(float(_MOCK_DC_DETAILS[c].get("hyperconv", {}).get("stor_used", 0) or 0) for c in MOCK_DC_CODES))

    cc_cap, cc_u, cm_cap, cm_u, cs_cap, cs_u, hc_cap, hc_u, hm_cap, hm_u, hs_cap, hs_u = _sum_classic_hyperconv()

    ibm_mem_t = ibm_mem_a = ibm_cpu_u = ibm_cpu_a = ibm_st_c = ibm_st_u = 0.0
    for code in MOCK_DC_CODES:
        p = _MOCK_DC_DETAILS[code].get("power") or {}
        if not p:
            continue
        ibm_mem_t += float(p.get("memory_total", 0) or 0)
        ibm_mem_a += float(p.get("memory_assigned", 0) or 0)
        ibm_cpu_u += float(p.get("cpu_used", 0) or 0)
        ibm_cpu_a += float(p.get("cpu_assigned", 0) or 0)
        ibm_st_c += float(p.get("storage_cap_tb", 0) or 0)
        ibm_st_u += float(p.get("storage_used_tb", 0) or 0)

    return {
        "overview": {
            "dc_count": len(MOCK_DC_CODES),
            "total_hosts": total_hosts,
            "total_vms": total_vms,
            "total_platforms": plat,
            "total_energy_kw": energy_ibm + energy_vc,
            "total_cpu_cap": cc_cap + hc_cap + ibm_cpu_a,
            "total_cpu_used": cc_u + hc_u + ibm_cpu_u,
            "total_ram_cap": cm_cap + hm_cap + ibm_mem_t,
            "total_ram_used": cm_u + hm_u + ibm_mem_a,
            "total_storage_cap": cs_cap + hs_cap + ibm_st_c,
            "total_storage_used": cs_u + hs_u + ibm_st_u,
        },
        "platforms": {
            "nutanix": {"hosts": 32, "vms": 850},
            "vmware": {"clusters": 7, "hosts": 30, "vms": 1130},
            "ibm": {"hosts": 10, "vios": 4, "lpars": 20},
        },
        "energy_breakdown": {"ibm_kw": energy_ibm, "vcenter_kw": energy_vc},
        "classic_totals": {
            "cpu_cap": cc_cap,
            "cpu_used": cc_u,
            "mem_cap": cm_cap,
            "mem_used": cm_u,
            "stor_cap": cs_cap,
            "stor_used": cs_u,
        },
        "hyperconv_totals": {
            "cpu_cap": hc_cap,
            "cpu_used": hc_u,
            "mem_cap": hm_cap,
            "mem_used": hm_u,
            "stor_cap": hs_cap,
            "stor_used": hs_u,
        },
        "ibm_totals": {
            "mem_total": ibm_mem_t,
            "mem_assigned": ibm_mem_a,
            "cpu_used": ibm_cpu_u,
            "cpu_assigned": ibm_cpu_a or 1.0,
            "stor_cap": ibm_st_c,
            "stor_used": ibm_st_u,
        },
    }
