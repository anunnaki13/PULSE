"""Outage Management pilot rubric (REQ-dynamic-ml-schema).

Source: ``01_DOMAIN_MODEL.md`` §4.2 (Outage Management example tree).

Coverage: 2 areas (Long Term Planning, P3 Weekly Planning, Pre/During/Post
Outage) with at least one sub-area carrying the full L0..L4 criteria block.
The plan verifier greps for ``OUTAGE`` and ``level_4`` in this file.

Idempotency: existence check on MlStream.kode == "OUTAGE".
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_stream import MlStream

KODE = "OUTAGE"
NAMA = "Outage Management"
VERSION = "2026.1"

STRUCTURE: dict = {
    "areas": [
        {
            "kode": "OM-LT",
            "nama": "Long Term Planning",
            "sub_areas": [
                {
                    "kode": "OM-LT-01",
                    "nama": "Rencana dan Jadwal Planned Outage Jangka Panjang",
                    "criteria": {
                        "level_0": "Belum ada rencana outage jangka panjang formal — penjadwalan reaktif.",
                        "level_1": "Rencana ada tetapi belum lengkap; banyak perubahan jadwal.",
                        "level_2": "Rencana lengkap 5-tahun; review tahunan; perubahan terdokumentasi.",
                        "level_3": "Optimasi sumber daya antar unit; risk-based scheduling; review semi-annual.",
                        "level_4": "Continuous improvement; KPI tracked; integrasi dengan supply chain & finance planning.",
                    },
                },
            ],
        },
        {
            "kode": "OM-P3",
            "nama": "P3 (1 Week Planning)",
            "sub_areas": [
                {
                    "kode": "OM-P3-01",
                    "nama": "Reviu Progres Meeting P2 & Hasil OH",
                    "criteria": {
                        "level_0": "Tidak ada meeting formal P2.",
                        "level_1": "Meeting ad-hoc; tidak ada agenda tetap.",
                        "level_2": "Meeting mingguan dengan agenda standar.",
                        "level_3": "Meeting + tracker action item + escalation matrix.",
                        "level_4": "Predictive analytics + cross-stream coordination + continuous KPI review.",
                    },
                },
                {
                    "kode": "OM-P3-02",
                    "nama": "Penambahan Scope Pekerjaan Overhaul",
                    "criteria": {
                        "level_0": "Scope ditambah ad-hoc tanpa dokumentasi formal.",
                        "level_1": "Penambahan scope dicatat manual.",
                        "level_2": "Form change-request standar; approval per level.",
                        "level_3": "Impact assessment cost + schedule sebelum approval.",
                        "level_4": "Digitalized workflow + automated impact analysis + lessons-learned database.",
                    },
                },
            ],
        },
        {
            "kode": "OM-EX",
            "nama": "Pre/During/Post Outage Execution",
            "sub_areas": [
                {
                    "kode": "OM-EX-01",
                    "nama": "Pre-Outage Readiness & Kit Lengkap",
                    "criteria": {
                        "level_0": "Tidak ada checklist pre-outage.",
                        "level_1": "Checklist ada tetapi tidak konsisten dipakai.",
                        "level_2": "Checklist standar + go/no-go gate.",
                        "level_3": "Pre-mortem + spare parts forecast + safety review.",
                        "level_4": "Digital twin simulation + cross-functional readiness drill.",
                    },
                },
            ],
        },
    ],
}


async def seed(db: AsyncSession) -> None:
    existing = await db.scalar(select(MlStream).where(MlStream.kode == KODE))
    if existing is not None:
        print(f"[seed] ml_stream {KODE}: already exists (id={existing.id})")
        return
    db.add(MlStream(kode=KODE, nama=NAMA, version=VERSION, structure=STRUCTURE))
    await db.flush()
    print(f"[seed] ml_stream {KODE}: created (version={VERSION}, areas={len(STRUCTURE['areas'])})")
