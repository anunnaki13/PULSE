# 04 — API Specification (FastAPI)

> REST API contract untuk SISKONKIN, dengan FastAPI sebagai backend. Versioning prefix `/api/v1`.

---

## 1. Konvensi Umum

- **Base URL:** `https://siskonkin.tenayan.local/api/v1`
- **Auth:** JWT via `Authorization: Bearer <token>` header (atau httpOnly cookie untuk web)
- **Format request/response:** JSON (UTF-8)
- **Pagination:** query params `?page=1&page_size=20`, response wrap `{ data: [...], meta: { total, page, ...} }`
- **Filter:** query params seperti `?status=submitted&bidang_id=...`
- **Sorting:** `?sort=-created_at` (minus = desc)
- **Error format:**
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Bobot indikator melebihi total perspektif",
      "details": {...}
    }
  }
  ```

### HTTP Status Codes
- `200` Success
- `201` Created
- `204` No Content (delete success)
- `400` Validation error
- `401` Unauthenticated
- `403` Forbidden (role tidak punya akses)
- `404` Not Found
- `409` Conflict (mis. submit ke periode yang sudah closed)
- `422` Unprocessable (data tidak valid bisnis-wise)
- `500` Server error

---

## 2. Authentication

### `POST /auth/login`
Login, dapat JWT.

**Request:**
```json
{ "email": "budi@pln.co.id", "password": "..." }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "full_name": "Budi Santoso",
    "email": "budi@pln.co.id",
    "bidang": { "id": "...", "code": "BID_OM_3", "name": "..." },
    "roles": ["pic_bidang"]
  }
}
```

### `POST /auth/refresh`
Refresh access token pakai refresh token.

### `POST /auth/logout`
Invalidate refresh token.

### `GET /auth/me`
Detail user yang login.

---

## 3. Master Data

### Bidang
- `GET    /bidang` — list semua bidang
- `GET    /bidang/{id}` — detail bidang
- `POST   /bidang` (admin) — create
- `PATCH  /bidang/{id}` (admin) — update
- `DELETE /bidang/{id}` (admin) — soft delete

### User Management
- `GET    /users` (admin) — list user dengan filter
- `POST   /users` (admin) — create user
- `PATCH  /users/{id}` (admin) — update
- `POST   /users/{id}/roles` (admin) — assign role
- `DELETE /users/{id}/roles/{role_id}` (admin) — revoke role

---

## 4. Konkin Template & Struktur

### `GET /konkin/templates`
List semua template Konkin per tahun.

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "tahun": 2026,
      "unit_code": "UP_TENAYAN",
      "judul": "...",
      "is_active": true,
      "locked": false
    }
  ]
}
```

### `GET /konkin/templates/{id}`
Detail template + perspektif + indikator (tree).

### `GET /konkin/templates/{id}/perspektif`
List perspektif untuk template tertentu.

### `GET /konkin/perspektif/{id}/indikator`
List indikator dalam satu perspektif.

### `GET /konkin/indikator/{id}`
Detail indikator + sub-indikator (jika agregat) + ml_stream (jika ML) + owners.

**Response (contoh untuk indikator agregat ML):**
```json
{
  "id": "uuid",
  "code": "ML_ASET_PEMBANGKIT",
  "nama": "Maturity Level Manajemen Aset Pembangkitan",
  "bobot": 25.0,
  "tipe": "maturity_level_kpi",
  "perspektif": { "id": "...", "code": "II", "name": "Model Business Innovation" },
  "owners": [
    { "bidang": { "code": "BID_OM_1", "name": "..." }, "role_in_process": "pic" }
  ],
  "sub_indikator": [
    {
      "id": "...", "code": "OUTAGE_MGMT", "nama": "Outage Management",
      "ml_stream": {
        "id": "...",
        "bobot_ml": 50, "bobot_kpi": 50,
        "structure": { "areas": [...] }
      }
    },
    ...
  ]
}
```

### `POST /konkin/templates`
(Super admin) Buat template baru. Bisa clone dari template tahun sebelumnya:
```json
{
  "tahun": 2027,
  "unit_code": "UP_TENAYAN",
  "clone_from_id": "uuid_template_2026"
}
```

### `PATCH /konkin/indikator/{id}`
Update bobot, formula, dll. Hanya boleh kalau template belum locked.

### `POST /konkin/templates/{id}/lock`
(Admin) Lock template — tidak boleh diubah lagi.

### `POST /konkin/templates/{id}/import-from-excel`
Import struktur dari kertas kerja Excel existing. Body multipart file.

---

## 5. Periode

### `GET /periode`
List periode (filter `?tahun=2026&triwulan=2`).

### `POST /periode`
(Admin) Buat periode baru.
```json
{
  "template_id": "uuid",
  "tahun": 2026, "triwulan": 2, "semester": 1,
  "tanggal_mulai": "2026-04-01",
  "tanggal_akhir": "2026-06-30",
  "deadline_self_assessment": "2026-07-05",
  "deadline_asesmen": "2026-07-15",
  "deadline_finalisasi": "2026-07-25"
}
```

### `PATCH /periode/{id}/status`
Ubah status periode (draft → aktif → self_assessment → asesmen → finalisasi → closed).

### `GET /periode/{id}/summary`
Ringkasan progres triwulan: berapa indikator selesai self-assessment, berapa diasesmen, berapa rekomendasi terbuka.

### `POST /periode/{id}/close`
Finalisasi & lock periode. Otomatis carry-over rekomendasi yang masih open ke periode berikutnya.

### `POST /periode/{id}/calculate-nko`
Trigger perhitungan NKO untuk periode ini (bisa dipanggil manual; juga auto-trigger setiap perubahan assessment).

---

## 6. Assessment Session — Inti Operasional

### `GET /assessment/sessions`
List sesi asesmen. Filter:
- `?periode_id=`
- `?bidang_id=` (default: bidang user yang login untuk PIC)
- `?status=draft|submitted|approved|...`
- `?indikator_id=`
- `?my_pic=true` (untuk PIC: hanya yang dia owner)
- `?my_asesor=true` (untuk asesor: hanya yang ditugaskan ke dia)

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "periode": { "id": "...", "tahun": 2026, "triwulan": 2 },
      "indikator": { "id": "...", "code": "EAF", "nama": "...", "tipe": "kpi_kuantitatif" },
      "bidang_pic": { "code": "BID_OM_3" },
      "self_assessment_status": "submitted",
      "asesor_status": "pending",
      "nilai_kontribusi": null,
      "deadline_self_assessment": "2026-07-05",
      "submitted_at": "2026-07-03T10:00:00Z"
    }
  ]
}
```

### `GET /assessment/sessions/{id}`
Detail lengkap satu sesi: target, self_assessment, asesor_review, recommendations terkait.

### `PATCH /assessment/sessions/{id}/self-assessment`
PIC update self-assessment (save draft).

**Request body:**
```json
{
  "self_assessment": {
    "realisasi": 84.7,
    "komponen": { "AH": 2150, "EPDH": 0, "EMDH": 5, "EFDH": 12 },
    "catatan_pic": "EAF tercapai sangat baik karena tidak ada FO besar",
    "link_eviden": "https://drive.google.com/file/abc"
  }
}
```

Untuk **maturity level**:
```json
{
  "self_assessment": {
    "areas": [
      {
        "code": "I1.1",
        "sub_areas": [
          {
            "code": "I1.1.1",
            "level": 3,
            "nilai_numerik": 3.5,
            "catatan": "Sudah ada rencana 3 tahun ke depan, terintegrasi dengan Reliability"
          }
        ]
      }
    ],
    "kpi_component": { ... },
    "catatan_pic": "..."
  }
}
```

### `POST /assessment/sessions/{id}/submit`
PIC submit untuk asesmen. Validasi: semua sub-area maturity level harus terisi (atau eksplisit ditandai N/A).

### `POST /assessment/sessions/{id}/withdraw`
PIC tarik kembali submission (kalau belum di-review asesor).

### `POST /assessment/sessions/{id}/asesor-review`
Asesor input review.

**Request body:**
```json
{
  "decision": "override",
  "nilai_final": 102.0,
  "catatan_asesor": "Komponen EFDH perlu dikoreksi karena ada outage yang...",
  "recommendations": [
    {
      "severity": "medium",
      "deskripsi": "Pertahankan tren EAF dengan PdM kuartalan",
      "action_items": [
        { "action": "Lakukan PdM turbin unit 1", "deadline": "2026-09-30" }
      ],
      "target_periode_id": "uuid_tw3"
    }
  ]
}
```

### `POST /assessment/sessions/{id}/return-for-revision`
Asesor kembalikan ke PIC dengan catatan.

### `GET /assessment/sessions/{id}/calculate`
Preview perhitungan nilai (tanpa save). Berguna saat PIC sedang isi.

---

## 7. Rekomendasi & Tindak Lanjut

### `GET /recommendations`
List. Filter:
- `?status=open|in_progress|...`
- `?severity=critical|high|...`
- `?bidang_id=` (default: bidang user untuk PIC)
- `?periode_id=`
- `?indikator_id=`

### `GET /recommendations/{id}`
Detail + history progress.

### `PATCH /recommendations/{id}/progress`
PIC update progress.
```json
{
  "progress_percent": 60,
  "notes": "Sudah lakukan PdM unit 1, jadwal unit 2 minggu depan",
  "status": "in_progress"
}
```

### `POST /recommendations/{id}/mark-completed`
PIC tandai selesai. Status → `pending_review`.

### `POST /recommendations/{id}/verify-close`
Asesor verify & close.
```json
{
  "asesor_close_notes": "Dokumentasi PdM sudah cukup, ditutup",
  "verified": true
}
```

### `POST /recommendations/{id}/carry-over`
Carry rekomendasi yang tidak selesai ke periode berikutnya.

---

## 8. Compliance Tracker

### `GET /compliance/laporan-definisi`
List jenis laporan rutin.

### `GET /compliance/submissions`
List submission. Filter `?periode_id=`, `?laporan_id=`.

### `POST /compliance/submissions`
Catat submission laporan.
```json
{
  "laporan_definisi_id": "uuid",
  "periode_id": "uuid",
  "tanggal_submit": "2026-07-06",
  "valid_data": true,
  "notes": "..."
}
```

### `GET /compliance/komponen-realisasi?periode_id=`
List nilai komponen compliance (PACA, Critical Event, dll) per periode.

### `PATCH /compliance/komponen-realisasi/{id}`
Update nilai realisasi komponen.

### `GET /compliance/summary?periode_id=`
Ringkasan total pengurang Compliance untuk periode.

---

## 9. NKO & Dashboard

### `GET /nko/snapshot/latest?periode_id=`
NKO terbaru untuk periode.

### `GET /nko/snapshots?periode_id=`
History snapshot NKO (untuk lihat perkembangan).

### `GET /dashboard/executive?periode_id=`
Data dashboard eksekutif.

**Response:**
```json
{
  "periode": { "tahun": 2026, "triwulan": 2 },
  "nko_total": 102.45,
  "nko_target": 100,
  "forecast_akhir_semester": 103.80,
  "pilars": [
    { "code": "I", "nama": "...", "bobot": 46, "nilai": 47.20, "trend_vs_prev": +0.5 },
    ...
  ],
  "top_performers": [
    { "indikator": "EAF", "pencapaian": 110 }
  ],
  "needs_attention": [
    { "indikator": "SFC Batubara", "pencapaian": 92 }
  ],
  "recommendations": {
    "total": 18, "open": 5, "in_progress": 7, "closed": 6,
    "critical_overdue": 2
  }
}
```

### `GET /dashboard/maturity-heatmap?tahun=2026`
Heatmap stream × triwulan untuk visualisasi.

### `GET /dashboard/trend?indikator_id=&tahun=`
Time series untuk satu indikator.

---

## 10. Reports & Export

### `GET /reports/nko-semester?periode_id=&format=pdf|excel|word`
Generate laporan NKO semester resmi.

### `GET /reports/assessment-sheet?session_id=&format=excel`
Export kertas kerja per sesi (mirror format Excel existing).

### `GET /reports/compliance-detail?periode_id=&format=excel`
Detail laporan compliance.

### `GET /reports/recommendation-tracker?periode_id=&format=excel`
Tracker rekomendasi.

---

## 11. AI Assistant

### `POST /ai/draft-justification`
Bantu PIC menulis justifikasi self-assessment.

**Request:**
```json
{
  "session_id": "uuid",
  "context_hint": "EAF tercapai 105% karena tidak ada FO besar"
}
```

**Response:**
```json
{
  "suggestion": "EAF unit Tenayan pada TW2 2026 mencapai 84.70%, melampaui target 80.27% (105.51%). Kinerja ini didukung oleh tidak terjadinya forced outage besar selama periode, didukung pelaksanaan PdM rutin yang konsisten...",
  "model_used": "google/gemini-2.5-flash",
  "tokens_used": 145
}
```

### `POST /ai/draft-recommendation`
Bantu asesor merumuskan rekomendasi.

### `POST /ai/anomaly-check`
Cek apakah nilai self-assessment di luar tren historis.

### `POST /ai/summarize-periode`
Generate executive summary untuk dashboard.

### `POST /ai/chat`
Chat session dengan konteks Pedoman Konkin (RAG).

**Request:**
```json
{
  "conversation_id": "uuid_optional",
  "message": "Bagaimana cara hitung EAF kalau ada outage maintenance non-tactical?",
  "context_type": "indikator_specific",
  "context_id": "indikator_eaf_uuid"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "answer": "Menurut Pedoman Pasal 1.1.g, EAF dihitung dengan formula...",
  "sources": [
    { "section": "1.1.g EAF", "content_snippet": "...", "page": 10 }
  ]
}
```

### `POST /ai/generate-action-plan`
Dari rekomendasi, generate action items terukur dan SMART.

### `GET /ai/conversations`
List conversation user.

### `GET /ai/conversations/{id}`
Detail conversation + messages.

---

## 12. Notification

### `GET /notifications`
List notifikasi user (unread first).

### `PATCH /notifications/{id}/read`
Mark as read.

### `PATCH /notifications/read-all`
Mark all as read.

---

## 13. Audit Log (Read-Only)

### `GET /audit-logs`
(Super admin / auditor) List audit log dengan filter.

### `GET /audit-logs/{id}`
Detail.

---

## 14. Health & Operational

### `GET /health`
Health check (database connection, redis, dll).

### `GET /health/detail` (admin)
Detail per komponen.

### `GET /metrics` (admin)
Prometheus-format metrics.

---

## 15. WebSocket (Real-time Updates)

### `WS /ws/dashboard?token=...`
Subscribe ke perubahan NKO real-time.

**Server push:**
```json
{
  "type": "nko_updated",
  "periode_id": "uuid",
  "nko_total": 102.55,
  "changed_indikator": "EAF"
}
```

### `WS /ws/notifications?token=...`
Push notifikasi real-time.

---

## 16. Rate Limiting & Security

- Rate limit per user: 100 req/min default; 1000 req/min untuk dashboard read.
- AI endpoints: 20 req/min per user (mencegah abuse OpenRouter quota).
- File upload tidak ada (sesuai keputusan: tidak handle evidence file).
- Semua endpoint mutating wajib HTTPS.
- CSRF protection untuk endpoint cookie-based auth.
- Input validation via Pydantic.
- SQL injection: pakai parameterized query (SQLAlchemy default).

---

## 17. OpenAPI / Swagger

FastAPI auto-generate `/api/v1/docs` (Swagger UI) dan `/api/v1/redoc`. Schema lengkap akan tersedia di sana.

Untuk **production**, dokumentasi OpenAPI bisa di-disable atau dilindungi via auth.

---

**Selanjutnya:** [`05_FRONTEND_ARCHITECTURE.md`](05_FRONTEND_ARCHITECTURE.md) — struktur React.
