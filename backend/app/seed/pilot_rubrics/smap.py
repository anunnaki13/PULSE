"""SMAP (Sistem Manajemen Anti Penyuapan) pilot rubric (REQ-dynamic-ml-schema).

Source: ``01_DOMAIN_MODEL.md`` §4.2 (SMAP example tree).

Coverage: one area (Klausul 4-7) with at least one sub-area carrying the
full L0..L4 criteria block. SMAP is a Compliance-tied rubric so it sits
under perspektif VI (pengurang).

Idempotency: existence check on MlStream.kode == "SMAP".
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_stream import MlStream

KODE = "SMAP"
NAMA = "Sistem Manajemen Anti Penyuapan"
VERSION = "2026.1"

STRUCTURE: dict = {
    "areas": [
        {
            "kode": "SMAP-PREV",
            "nama": "Pencegahan (Klausul 4.1, 4.2, 6.2, 7.4, 7.5)",
            "sub_areas": [
                {
                    "kode": "SMAP-PREV-01",
                    "nama": "Informasi Terdokumentasi SMAP — Buku Manual Utama",
                    "criteria": {
                        "level_0": "Tidak ada buku manual SMAP atau buku kadaluarsa.",
                        "level_1": "Buku manual ada tetapi tidak lengkap; review tidak rutin.",
                        "level_2": "Buku manual lengkap dengan semua klausul; review tahunan.",
                        "level_3": "Buku manual + tracking versi + akses online + sosialisasi terstruktur.",
                        "level_4": "Continuous improvement; integrated dengan ISO 37001 audit cycle; benchmarking.",
                    },
                },
                {
                    "kode": "SMAP-PREV-02",
                    "nama": "Pelatihan Anti Penyuapan",
                    "criteria": {
                        "level_0": "Tidak ada program pelatihan formal.",
                        "level_1": "Pelatihan ad-hoc; tidak ada kurikulum tetap.",
                        "level_2": "Pelatihan tahunan untuk semua pegawai; kurikulum standar.",
                        "level_3": "Pelatihan per-level + test kompetensi + tracking attendance.",
                        "level_4": "Adaptive learning + simulasi kasus + KPI behavior change.",
                    },
                },
            ],
        },
        {
            "kode": "SMAP-DETECT",
            "nama": "Deteksi & Pelaporan",
            "sub_areas": [
                {
                    "kode": "SMAP-DETECT-01",
                    "nama": "Whistleblowing System (WBS)",
                    "criteria": {
                        "level_0": "Tidak ada saluran WBS formal.",
                        "level_1": "Email/telpon tetapi tanpa proteksi pelapor.",
                        "level_2": "Sistem WBS dengan proteksi identitas pelapor + SLA respons.",
                        "level_3": "Sistem WBS + investigasi independen + tracking penyelesaian.",
                        "level_4": "Multi-channel WBS + analytics + integrasi dengan compliance dashboard.",
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
