# 07 — AI Integration (LLM Strategy)

> Strategi integrasi LLM ke SISKONKIN: bukan sebagai gimmick, tapi sebagai **akselerator workflow asesmen** yang membantu PIC dan asesor bekerja lebih cepat, lebih konsisten, dan lebih cerdas.

---

## 1. Filosofi Integrasi AI

Tiga prinsip kunci:

1. **AI sebagai asisten, bukan pengambil keputusan.** Setiap saran AI harus selalu bisa di-edit, di-tolak, atau di-override oleh manusia. Audit log mencatat mana yang AI-assisted.

2. **AI berbasis konteks domain Konkin.** Bukan general-purpose chatbot — semua prompt diberi konteks Pedoman Konkin, struktur indikator, dan data historis unit. Pakai RAG (Retrieval-Augmented Generation).

3. **Cost-conscious routing.** Pakai model murah (Gemini 2.5 Flash) untuk task rutin, model premium (Claude Sonnet) hanya saat kompleksitas tinggi. Target: **< Rp 50.000 per bulan untuk biaya AI** di awal MVP.

---

## 2. Provider & Model Strategy

### Provider: OpenRouter

OpenRouter dipilih karena:
- Single API untuk akses ke banyak model (Anthropic, Google, Meta, dll)
- Rate limiting & quota terpusat
- Pricing transparan dan kompetitif
- Failover jika satu provider down

### Model Routing

| Use Case | Model | Alasan |
|----------|-------|--------|
| Draft justifikasi (catatan pendek) | `google/gemini-2.5-flash` | Cepat, murah, cukup untuk task sederhana |
| Draft rekomendasi | `google/gemini-2.5-flash` | Idem |
| Anomaly detection (rule + LLM hybrid) | `google/gemini-2.5-flash` | Inference cepat, structured output |
| Smart summary periode | `anthropic/claude-sonnet-4` | Butuh nuance, ringkasan eksekutif berkualitas |
| Chat RAG dengan Pedoman | `anthropic/claude-sonnet-4` | Reasoning bagus, hallucination rendah |
| Action plan generator (SMART) | `anthropic/claude-sonnet-4` | Butuh structure & domain understanding |
| Embedding untuk RAG | `text-embedding-3-small` (OpenAI via OpenRouter) atau `voyage-2` | Murah & quality bagus |

### Estimasi Biaya (untuk skala UP Tenayan)

Asumsi penggunaan per bulan:
- 200 draft justification × 500 input + 300 output tokens × Gemini Flash
- 50 draft recommendation × 800 + 500 tokens × Gemini Flash
- 20 chat sessions × 5 turns × 2000 + 800 tokens × Claude Sonnet
- 4 summary periode × 8000 + 2000 tokens × Claude Sonnet
- ~100 anomaly checks × 1500 + 200 tokens × Gemini Flash

**Estimasi total:** ~$3-5 per bulan (Rp 50.000 - 80.000) di awal. Naik proporsional dengan adoption.

---

## 3. Use Case Detail

### 3.1 Draft Justifikasi (PIC)

**Trigger:** PIC klik tombol AI Assist saat mengisi catatan self-assessment.

**Input ke LLM:**
```
{
  "indikator": {
    "code": "EAF",
    "nama": "Equivalent Availability Factor",
    "formula": "...",
    "polaritas": "positif"
  },
  "values": {
    "target": 80.27,
    "realisasi": 84.70,
    "pencapaian_persen": 105.51,
    "komponen": {"AH": 2150, "EFDH": 12, ...}
  },
  "history": [
    { "periode": "TW1 2026", "realisasi": 82.1 },
    { "periode": "TW4 2025", "realisasi": 79.8 }
  ],
  "user_hint": "EAF tercapai sangat baik karena tidak ada FO besar"
}
```

**Prompt template:**
```
Anda adalah asisten penulisan laporan kinerja PT PLN Nusantara Power. 
Tugas Anda: tuliskan justifikasi self-assessment indikator yang ringkas, 
profesional, dan berbasis data.

Indikator: {indikator.nama}
Periode: {periode}
Target: {target} | Realisasi: {realisasi} | Pencapaian: {pencapaian}%

Konteks tambahan dari PIC: {user_hint}

Tren historis:
{history}

Tuliskan justifikasi dalam Bahasa Indonesia formal, 3-5 kalimat:
1. Menyebutkan capaian numerik dengan benar
2. Mengidentifikasi faktor pendukung/penghambat
3. Bandingkan dengan tren periode sebelumnya jika relevan
4. Hindari jargon yang tidak ada di pedoman; gunakan istilah teknis dengan tepat

JANGAN tambahkan rekomendasi atau saran perbaikan — itu tugas asesor.
```

**Output:** teks justifikasi yang bisa langsung dipakai atau di-edit.

### 3.2 Draft Rekomendasi (Asesor)

**Trigger:** Asesor di form review, klik AI Assist untuk merumuskan rekomendasi.

**Input:**
```
{
  "indikator": { ... },
  "self_assessment_pic": { ... },
  "asesor_decision": "override",
  "asesor_nilai_final": 102.0,
  "gap_analysis": "Realisasi 84.7%, di bawah ekspektasi best practice 87%",
  "previous_recommendations": [
    { "periode": "TW1 2026", "deskripsi": "Tingkatkan PdM" }
  ]
}
```

**Prompt template:**
```
Anda adalah asesor senior Konkin PT PLN Nusantara Power. 
Tugas: rumuskan rekomendasi konstruktif untuk PIC bidang.

Konteks indikator dan capaian: {context}

Rekomendasi sebelumnya yang sudah diberikan: {previous_recommendations}

Hasilkan rekomendasi dengan struktur:
1. **Deskripsi**: 1-2 kalimat menyebutkan area improvement
2. **Action items**: 2-4 langkah terukur (SMART), masing-masing dengan deadline indikatif
3. **Target outcome**: hasil yang diharapkan di periode berikutnya

Severity yang sesuai (low/medium/high/critical) — beri saran berbasis gap.

Hindari rekomendasi yang sama persis dengan periode sebelumnya. 
Eskalasi atau spesifikasi jika rekomendasi serupa belum berhasil.

Respon dalam JSON terstruktur.
```

**Output JSON:**
```json
{
  "severity": "medium",
  "deskripsi": "Tingkatkan ketepatan eksekusi PdM untuk menstabilkan EAF di atas 85%",
  "action_items": [
    { "action": "Lakukan PdM kuartalan untuk turbin unit 1 dan 2", "deadline": "TW3 2026" },
    { "action": "Tingkatkan kualitas pelaporan EFDH secara harian via Navitas", "deadline": "TW3 2026" },
    { "action": "Audit standard job overhaul terakhir untuk identifikasi gap", "deadline": "TW2 akhir" }
  ],
  "target_outcome": "EAF stabil ≥ 85%, EFDH < 0.5%"
}
```

### 3.3 Anomaly Detection

**Trigger:** Otomatis saat PIC submit self-assessment, atau saat asesor membuka antrian.

**Logic Hybrid:**
1. **Rule-based check (cepat, gratis):**
   - Realisasi vs target deviasi > 30%? → flag.
   - Realisasi vs rata-rata historis 4 periode > 2 std dev? → flag.
   - Sub-area maturity level naik > 1.5 level dalam 1 triwulan? → flag.
   - Komponen formula tidak konsisten matematis? → flag.

2. **LLM check (untuk yang sudah terflag rule):**
   - LLM diberi konteks data + flag → klasifikasi: `legitimate_improvement`, `data_entry_error`, `needs_verification`, `suspicious`.

**Output:** Badge warning di Asesor Workspace dengan alasan spesifik.

```
⚠️  Anomali Terdeteksi
Realisasi EAF naik 12% dari TW1 (82.1%) ke TW2 (84.7%).
Walau positif, kenaikan ini lebih tinggi dari rata-rata fluktuasi.
Saran: verifikasi komponen EFDH dengan data Navitas.
```

### 3.4 Smart Summary Periode

**Trigger:** Setelah periode di-close, atau saat manajer unit klik "Generate Executive Summary".

**Input:** Snapshot NKO + breakdown semua pilar + top performers + needs attention + rekomendasi.

**Prompt:**
```
Anda menulis executive summary untuk laporan triwulan PT PLN Nusantara Power 
PLTU Tenayan kepada manajemen.

Data:
{breakdown_data}

Tuliskan summary dalam Bahasa Indonesia formal, struktur:

## Ringkasan Kinerja TW{n} {tahun}
Paragraf pembuka: NKO total, vs target, vs periode sebelumnya.

## Performa per Pilar
Bullet points: highlight kontribusi positif & area perhatian per pilar.

## Capaian Tertinggi & Tantangan Utama
- Capaian terbaik: ...
- Tantangan utama: ...

## Tindak Lanjut Strategis
Rekomendasi level eksekutif untuk triwulan berikutnya.

Total: 400-600 kata. Faktual, tidak overclaim, gunakan angka spesifik.
```

### 3.5 Chat dengan Pedoman Konkin (RAG)

**Trigger:** User buka `/ai/chat`, ajukan pertanyaan.

**Pipeline:**
1. Query embedding (sekali untuk pertanyaan user)
2. Search top-k (k=5) chunk Pedoman dari `pedoman_chunk` via pgvector cosine similarity
3. Inject chunk sebagai context ke prompt
4. LLM jawab dengan citation

**Prompt template:**
```
Anda asisten yang menjawab pertanyaan tentang Pedoman Penilaian Kontrak Kinerja
PT PLN Nusantara Power (Peraturan Direksi 0019.P/DIR/2025).

Konteks dari Pedoman:
---
[Section 1.1.g halaman 10]
EAF (Equivalent Availability Factor) adalah...
[formula]
---
[Section ...]

Pertanyaan user: {question}

Aturan:
1. Jawab HANYA berdasarkan konteks di atas. Jangan mengarang.
2. Sebut sumber: "(Pedoman bagian X.Y, hal Z)"
3. Jika konteks tidak cukup, katakan jujur: "Informasi ini tidak ditemukan 
   secara eksplisit di Pedoman. Mohon konsultasi dengan DIVPKP."
4. Bahasa Indonesia formal.
```

**Frontend:** chat UI dengan source citation yang bisa di-click untuk lihat snippet asli.

### 3.6 Action Plan Generator (SMART)

**Trigger:** Setelah rekomendasi dibuat, klik "Detailkan jadi Action Plan SMART".

**Output:** Action items terukur dengan kriteria SMART (Specific, Measurable, Achievable, Relevant, Time-bound).

```json
[
  {
    "action": "Lakukan PdM kuartalan turbin unit 1 dan 2",
    "specific": "PdM meliputi vibration analysis, oil analysis, infrared thermography",
    "measurable": "100% komponen kritis di-cover, hasil di-log di sistem CMMS",
    "achievable": "Resource teknisi dan tools sudah tersedia",
    "relevant": "Mendukung pencapaian EAF ≥ 85%",
    "time_bound": "Selesai sebelum 30 September 2026 (TW3)",
    "responsible": "Supervisor PdM Mekanik",
    "deliverable": "Laporan PdM 2 unit + rekomendasi corrective action"
  }
]
```

---

## 4. RAG (Retrieval-Augmented Generation) Setup

### 4.1 Source Documents

Dokumen yang di-index ke `pedoman_chunk`:
1. **Pedoman Penilaian Kontrak Kinerja** (Peraturan Direksi 0019.P/DIR/2025) — sumber utama
2. **Konkin Tenayan 2026** — struktur indikator & target
3. **Lampiran Kriteria Level Indikator** — rubrik maturity level
4. *(Future)* SOP-SOP operasional unit yang relevan

### 4.2 Chunking Strategy

```python
# scripts/index_pedoman.py
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " "],
)

# Pre-process: extract section markers from Pedoman text
# Setiap chunk dilabel dengan section/page metadata

chunks = splitter.split_text(pedoman_text)

for chunk in chunks:
    embedding = embed_text(chunk.text)  # via OpenRouter
    db.execute("""
        INSERT INTO pedoman_chunk (source_doc, section, chunk_index, content, embedding, metadata)
        VALUES (...)
    """)
```

### 4.3 Retrieval

```python
async def retrieve_relevant_chunks(query: str, k: int = 5) -> list[Chunk]:
    query_embedding = await embed_text(query)
    return await db.fetch_all("""
        SELECT id, section, content, metadata,
               embedding <=> $1::vector AS distance
        FROM pedoman_chunk
        ORDER BY embedding <=> $1::vector
        LIMIT $2
    """, query_embedding, k)
```

### 4.4 Hybrid Search (Optional Enhancement)

Tambah BM25 keyword search untuk istilah teknis spesifik (mis. "EFOR", "DMN") yang mungkin tidak tertangkap embedding semantic well. Combine dengan reciprocal rank fusion.

---

## 5. Backend Architecture for AI

```python
# app/services/ai/
├── __init__.py
├── client.py                  # OpenRouter HTTP client wrapper
├── router.py                  # Route ke model yang tepat
├── prompts/                   # Template prompts
│   ├── draft_justification.py
│   ├── draft_recommendation.py
│   ├── summary_periode.py
│   ├── chat_rag.py
│   └── anomaly_check.py
├── rag/
│   ├── retrieval.py
│   ├── embedding.py
│   └── indexer.py             # Script untuk index ulang Pedoman
├── anomaly/
│   ├── rules.py               # Rule-based checks
│   └── llm_classifier.py
└── audit.py                   # Log ke ai_suggestion_log
```

### Client Wrapper Example

```python
# app/services/ai/client.py
import httpx
from typing import Literal

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        response_format: dict | None = None,
    ) -> dict:
        resp = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://siskonkin.tenayan.local",
                "X-Title": "SISKONKIN",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **({"response_format": response_format} if response_format else {}),
            },
        )
        resp.raise_for_status()
        return resp.json()
```

### Service Example

```python
# app/services/ai/draft_justification.py
async def draft_justification(session_id: UUID, user_hint: str) -> str:
    session = await get_assessment_session(session_id)
    history = await get_history(session.indikator_id, limit=4)
    
    prompt = JUSTIFICATION_PROMPT.format(
        indikator=session.indikator,
        values=session.self_assessment,
        history=history,
        user_hint=user_hint,
    )
    
    result = await openrouter.complete(
        model="google/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )
    
    suggestion = result["choices"][0]["message"]["content"]
    
    # Audit log
    await log_ai_suggestion(
        user_id=current_user.id,
        suggestion_type="justification_draft",
        context_entity_id=session_id,
        prompt=prompt,
        suggestion_text=suggestion,
        model_used="google/gemini-2.5-flash",
    )
    
    return suggestion
```

---

## 6. Privacy & Data Security

### Data yang TIDAK boleh dikirim ke LLM:
- ❌ NIP, nomor pegawai pribadi (anonimisasi → "PIC Bidang OM-3")
- ❌ Email pribadi
- ❌ Data finansial detail kontrak vendor (Rp spesifik OK, nama vendor masked)
- ❌ Data audit yang sedang dalam investigasi

### Data yang BOLEH dikirim:
- ✅ Indikator kinerja (KPI, formula, target, realisasi)
- ✅ Struktur maturity level (kriteria deskriptif)
- ✅ Catatan teknis self-assessment (setelah PII filter)
- ✅ Snapshot NKO agregat

### Implementasi:
- **PII Masking layer** sebelum kirim ke LLM
- **Audit trail** semua AI request di `ai_suggestion_log`
- **Rate limiting** per user (20 req/min) — mencegah data exfiltration
- **No-log policy** dengan OpenRouter di header request

---

## 7. UX Pattern: AI Assist Drawer

Di setiap form yang punya AI assist:

```
┌──────────────────────────────────────────────────┐
│ Catatan PIC:                                     │
│ ┌──────────────────────────────────────────────┐│
│ │ [textarea]                                   ││
│ │                                              ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ [💡 AI Assist]  ← klik buka drawer kanan        │
└──────────────────────────────────────────────────┘

       ┌──────────────────────────────────┐
       │  Drawer kanan                    │
       │  ─────────────────────────       │
       │  💡 Saran AI                     │
       │                                  │
       │  [⏳ Generating...]              │
       │  → [text suggestion]              │
       │                                  │
       │  [✏️ Edit]                       │
       │  [✅ Pakai sebagai catatan]      │
       │  [❌ Tolak]                      │
       │                                  │
       │  💡 Konteks yang dipakai:        │
       │  - Indikator: EAF                │
       │  - Realisasi: 84.7%              │
       │  - 4 periode historis            │
       └──────────────────────────────────┘
```

Transparansi konteks penting — user tahu apa yang di-share ke AI.

---

## 8. Roadmap AI Features

| Fase | Fitur | Kompleksitas |
|------|-------|-------------|
| MVP (Fase 1-3) | Draft justifikasi + draft rekomendasi | Low |
| MVP+1 (Fase 4) | Anomaly detection rule-based + LLM | Medium |
| Phase 2 (Fase 5) | RAG chat dengan Pedoman | Medium |
| Phase 2 | Smart summary periode | Medium |
| Phase 2 | Action plan generator SMART | Medium |
| Future | Forecasting NKO (time series ML) | High |
| Future | Multi-unit benchmarking AI | High |
| Future | Voice-input untuk catatan (Whisper) | Medium |
| Future | Auto-translate Bahasa-English untuk laporan internasional | Low |

---

## 9. Monitoring & Quality Control

### Metrics to Track:
- Acceptance rate per AI suggestion type (target: > 60% untuk draft, > 40% untuk anomaly)
- Average latency per request (target: < 5 detik)
- Cost per user per month
- User satisfaction (thumbs up/down per saran)

### A/B Testing Setup:
- Compare prompt variations
- Compare model performance (Gemini Flash vs Claude Sonnet untuk task tertentu)
- Track downstream impact (apakah suggestion AI meningkatkan kualitas catatan?)

---

## 10. Fallback & Graceful Degradation

Kalau OpenRouter down atau quota habis:
- Tombol AI Assist tetap muncul tapi disable dengan tooltip "Layanan AI sementara tidak tersedia"
- Form tetap fungsi sepenuhnya tanpa AI
- Notification ke admin via email/Slack
- Log error dengan retry exponential backoff

---

**Selanjutnya:** [`08_DEPLOYMENT.md`](08_DEPLOYMENT.md) — Docker Compose & deployment.
