"""OpenRouter client with deterministic local mock mode."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass(frozen=True)
class LlmResult:
    text: str
    model: str
    fallback_used: bool
    latency_ms: int
    estimated_cost_usd: float
    error: str | None = None


def ai_mode() -> str:
    key = settings.OPENROUTER_API_KEY.get_secret_value()
    if settings.AI_MOCK_MODE:
        return "mock"
    if key:
        return "openrouter"
    return "unavailable"


def ai_available() -> bool:
    return ai_mode() in {"mock", "openrouter"}


async def complete_chat(
    *,
    use_case: str,
    messages: list[dict[str, str]],
    complex: bool = False,
    response_format: dict | None = None,
) -> LlmResult:
    model = settings.OPENROUTER_COMPLEX_MODEL if complex else settings.OPENROUTER_ROUTINE_MODEL
    started = time.perf_counter()
    mode = ai_mode()
    if mode == "mock":
        return LlmResult(
            text=_mock_response(use_case),
            model=f"{model}:mock",
            fallback_used=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
            estimated_cost_usd=0.0,
        )
    if mode == "unavailable":
        return LlmResult(
            text="",
            model=model,
            fallback_used=True,
            latency_ms=0,
            estimated_cost_usd=0.0,
            error="openrouter_api_key_missing",
        )

    payload: dict = {"model": model, "messages": messages, "temperature": 0.2}
    if response_format is not None:
        payload["response_format"] = response_format
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.get_secret_value()}",
        "HTTP-Referer": settings.APP_BASE_URL,
        "X-Title": "PULSE",
        "X-OpenRouter-Title": "PULSE",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            usage = body.get("usage") or {}
            cost = float(usage.get("cost") or 0.0)
            return LlmResult(
                text=str(content),
                model=str(body.get("model") or model),
                fallback_used=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                estimated_cost_usd=cost,
            )
    except Exception as exc:
        return LlmResult(
            text=_mock_response(use_case),
            model=f"{model}:fallback",
            fallback_used=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
            estimated_cost_usd=0.0,
            error=str(exc)[:1000],
        )


def _mock_response(use_case: str) -> str:
    if use_case == "draft_recommendation":
        return (
            '{"severity":"medium","deskripsi":"Perkuat tindak lanjut kinerja indikator melalui review mingguan berbasis data aktual dan target.",'
            '"action_items":[{"action":"Susun rencana aksi korektif berbasis gap realisasi terhadap target dan tetapkan PIC pelaksana.","deadline":null,"owner_user_id":null}],'
            '"target_outcome":"Gap kinerja menurun pada periode evaluasi berikutnya dan evidence tindak lanjut terdokumentasi."}'
        )
    if use_case == "anomaly_check":
        return '{"classification":"needs_verification","risk_score":62,"reasons":["Deviasi realisasi terhadap target perlu dikonfirmasi dengan catatan operasi.","Tidak ada evidence baru yang boleh diasumsikan oleh AI."]}'
    if use_case == "inline_help":
        return (
            '{"apa_itu":"Indikator ini digunakan untuk menilai pencapaian kinerja unit terhadap target Konkin.",'
            '"formula_explanation":"Gunakan formula dan polaritas yang tersimpan pada master indikator; nilai lebih tinggi tidak selalu lebih baik untuk polaritas negatif.",'
            '"best_practice":"Isi realisasi dari sumber operasi resmi, sertakan catatan singkat, dan pastikan alasan tidak dinilai jelas bila sub-area tidak berlaku.",'
            '"common_pitfalls":"Kesalahan umum meliputi tertukar target/realisasi, mengabaikan polaritas negatif, dan menulis justifikasi tanpa angka pembanding.",'
            '"related_indikator":[]}'
        )
    if use_case == "comparative_analysis":
        return "Kinerja indikator perlu dibandingkan dengan periode sebelumnya menggunakan arah polaritas yang benar. Gap terhadap target menjadi fokus utama karena menentukan prioritas tindak lanjut. Jika tren membaik, catatan tetap perlu menjelaskan program yang berkontribusi. Jika tren menurun, rekomendasi harus mengarah pada tindakan korektif yang terukur."
    if use_case == "rag_chat":
        return "Berdasarkan Pedoman Konkin, penilaian harus mengikuti struktur pilar, bobot indikator, dan formula polaritas yang sudah ditetapkan. Untuk maturity level, nilai diambil dari asesmen sub-area dan harus disertai catatan yang dapat diverifikasi. Jika komponen tidak dinilai, bobot atau rata-rata perlu dinormalisasi sesuai aturan agregasi."
    if use_case == "periode_summary":
        return (
            "Ringkasan eksekutif periode ini menunjukkan bahwa posisi NKO masih dapat dikendalikan, namun kualitas kesimpulan sangat bergantung pada kelengkapan assessment, status review asesor, dan disiplin input PIC di setiap stream. "
            "Kontribusi utama tetap berasal dari Pilar I, Pilar II, dan Pilar V sehingga perubahan kecil pada indikator berbobot besar dapat menggeser nilai akhir secara material. Karena itu, pembacaan dashboard tidak boleh berhenti pada angka total NKO, tetapi perlu melihat pilar, indikator, polaritas, dan catatan justifikasi yang menyertai realisasi. "
            "Untuk indikator kuantitatif, target dan realisasi harus diperiksa dengan formula yang benar. Indikator berpolaritas positif memakai arah pencapaian terhadap target, indikator negatif harus membaca penurunan realisasi sebagai perbaikan, sedangkan indikator range based perlu melihat kedekatan nilai terhadap target ideal. "
            "Jika ada realisasi yang tampak sangat tinggi atau sangat rendah, asesor sebaiknya meminta klarifikasi sumber operasi sebelum menyetujui nilai. AI hanya membantu menyusun narasi dan prioritas, bukan menggantikan validasi dokumen resmi atau keputusan asesor. "
            "Pada area maturity level, perhatian utama adalah kelengkapan sub-area, konsistensi level 0 sampai 4, dan normalisasi bobot ketika sebagian komponen tidak dinilai. Stream seperti Outage Management, Reliability, Efficiency, WPC, Operation, Energi Primer, LCCM, SCM, Lingkungan, K3, Keamanan, Bendungan, DPP, HCR, dan OCR memiliki struktur kriteria berbeda, sehingga perbandingan harus dilakukan di dalam konteks stream masing-masing. "
            "HCR dan OCR juga perlu dibaca sebagai kesiapan organisasi, bukan sekadar skor administratif, karena gap pada workforce planning, talent, performance, reward, industrial relation, organization design, dan OWM akan memengaruhi kesiapan eksekusi program unit. "
            "Komponen compliance perlu dipantau sebagai pengurang. Keterlambatan laporan, ketidaksesuaian dokumen, atau status submission yang belum tuntas dapat menekan nilai walaupun pilar kinerja utama terlihat baik. "
            "Prioritas tindak lanjut yang disarankan adalah menyelesaikan session yang belum direview, menutup gap indikator dengan deviasi terbesar, membuat rekomendasi SMART untuk area risiko tinggi, dan menetapkan PIC serta tenggat yang realistis. "
            "Setiap rekomendasi sebaiknya memiliki baseline, target antara, pemilik, batas waktu, dan indikator keberhasilan yang bisa dicek kembali pada rapat kinerja. "
            "Untuk gap yang lintas bidang, manajer unit perlu menunjuk koordinator agar tindak lanjut tidak berhenti di komentar asesor. "
            "Apabila data masih dummy atau belum final, status tersebut harus disebut jelas dalam catatan supaya pembaca tidak menganggap angka sebagai hasil audit final. "
            "Manajemen unit sebaiknya menggunakan ringkasan ini sebagai bahan rapat mingguan: cek indikator berbobot besar, cek stream maturity yang belum lengkap, cek compliance yang berpotensi menjadi pengurang, lalu minta update status rekomendasi sampai closed atau carry-over. "
            "Dengan cara ini, snapshot periode berikutnya akan lebih representatif, tindak lanjut lebih mudah diaudit, dan dashboard dapat menjadi alat kendali kinerja harian, bukan hanya rekap penilaian akhir."
        )
    if use_case == "action_plan":
        return (
            '{"severity":"high","deskripsi":"Susun rencana aksi SMART untuk menutup gap indikator prioritas berdasarkan hasil asesmen periode berjalan.",'
            '"action_items":[{"action":"Tetapkan baseline gap dan PIC tindak lanjut untuk indikator dengan deviasi terbesar.","deadline":null,"owner_user_id":null},'
            '{"action":"Lakukan review mingguan sampai status rekomendasi minimal in_progress dan evidence berupa tautan resmi tersedia.","deadline":null,"owner_user_id":null}],'
            '"target_outcome":"Gap indikator prioritas turun pada periode berikutnya dan seluruh tindak lanjut tercatat dalam tracker rekomendasi."}'
        )
    return "Berdasarkan target dan realisasi yang tersedia, capaian indikator perlu dijelaskan secara formal dengan menonjolkan gap utama terhadap target. Catatan sebaiknya menyebutkan konteks operasional yang dapat diverifikasi tanpa menambah bukti yang belum tersedia. Tindak lanjut perlu diarahkan pada pemulihan kinerja periode berjalan dan pencegahan deviasi berulang. Draft ini bersifat saran dan tetap perlu ditinjau oleh PIC sebelum disimpan."
