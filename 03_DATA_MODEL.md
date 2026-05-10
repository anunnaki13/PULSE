# 03 — Data Model (PostgreSQL Schema)

> Schema database PostgreSQL 16+ dengan dukungan JSONB untuk fleksibilitas struktur maturity level yang berbeda-beda per stream.

---

## 1. Prinsip Desain Schema

1. **Normalisasi untuk entitas stabil** (user, bidang, periode) — tabel relasional klasik.
2. **JSONB untuk struktur dinamis** (kriteria maturity level per stream, sub-area) — karena setiap stream berbeda.
3. **Soft delete** untuk semua entitas penting (`deleted_at TIMESTAMP`) — tidak boleh kehilangan history.
4. **Audit columns** di semua tabel: `created_at`, `updated_at`, `created_by`, `updated_by`.
5. **Versioning** struktur Konkin per tahun — schema bisa berubah di tahun depan tanpa break data tahun lalu.
6. **UUID** untuk primary key (lebih aman untuk URL publik & merge antar environment).

## 2. Skema Visual (ERD Sederhana)

```
┌─────────┐    ┌────────────┐    ┌──────────────┐
│ users   │────│user_roles  │────│   roles      │
└────┬────┘    └────────────┘    └──────────────┘
     │
     │ belongs to
     ▼
┌─────────────┐    ┌──────────────────┐
│  bidang     │────│ indikator_owners │ (M-to-M dengan indikator)
└─────────────┘    └────────┬─────────┘
                            │
                            ▼
┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ konkin_template  │────│ perspektif      │────│ indikator       │
│ (per tahun)      │    │ (per template)  │    │ (per perspektif)│
└──────────────────┘    └─────────────────┘    └────────┬────────┘
                                                         │
                                                         │ kalau tipe ML
                                                         ▼
                                              ┌──────────────────┐
                                              │ ml_stream        │
                                              │ (struktur JSONB) │
                                              └──────────────────┘

┌──────────────────┐
│ periode          │ (TW1/TW2/TW3/TW4 per tahun)
└────────┬─────────┘
         │
         ▼
┌─────────────────────┐
│ assessment_session  │ (1 per periode × indikator × bidang)
└──────────┬──────────┘
           │
           ├── self_assessment_data  (JSONB, isi sesuai tipe indikator)
           ├── asesor_review         (JSONB)
           └── recommendations       (1-many)
```

---

## 3. SQL DDL Lengkap

### 3.1 Tabel Master User & Auth

```sql
-- Extension untuk UUID & enkripsi
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS & ACCESS CONTROL
-- ============================================================

CREATE TABLE bidang (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,        -- e.g. 'BID_OM_3'
    name VARCHAR(255) NOT NULL,              -- e.g. 'Bidang Operasi & Maintenance OM-3'
    parent_id UUID REFERENCES bidang(id),    -- untuk sub-bidang
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    -- 'super_admin', 'admin_unit', 'pic_bidang', 'asesor', 'manajer_unit', 'viewer'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nip VARCHAR(50) UNIQUE,                  -- nomor pegawai
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bidang_id UUID REFERENCES bidang(id),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_bidang ON users(bidang_id) WHERE deleted_at IS NULL;
```

### 3.2 Struktur Konkin (Master Data)

```sql
-- Template Konkin per tahun (snapshot struktur)
CREATE TABLE konkin_template (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tahun INTEGER NOT NULL,
    unit_code VARCHAR(50) NOT NULL,         -- 'UP_TENAYAN'
    nomor_dokumen VARCHAR(100),             -- 'FMZ-12.1.2.1'
    judul VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    locked BOOLEAN DEFAULT FALSE,           -- true = tidak bisa diubah lagi
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tahun, unit_code)
);

-- 5 Pilar BUMN + Compliance
CREATE TABLE perspektif (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES konkin_template(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,              -- 'I', 'II', 'III', 'IV', 'V', 'VI'
    name VARCHAR(255) NOT NULL,             -- 'Economic & Social Value'
    bobot DECIMAL(5,2) NOT NULL,            -- 46.00
    sifat VARCHAR(20) DEFAULT 'penambah',   -- 'penambah' | 'pengurang'
    bobot_max_pengurang DECIMAL(5,2),       -- untuk Compliance: -10
    urutan INTEGER NOT NULL,
    UNIQUE(template_id, code)
);

-- Indikator (Level 1: bisa berupa indikator langsung atau agregat)
CREATE TABLE indikator (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    perspektif_id UUID NOT NULL REFERENCES perspektif(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,              -- 'EAF', 'BPP', 'OUTAGE_ML'
    nama VARCHAR(500) NOT NULL,
    bobot DECIMAL(5,2) NOT NULL,
    polaritas VARCHAR(20),                  -- 'positif' | 'negatif' | NULL untuk ML
    tipe VARCHAR(50) NOT NULL,
    -- 'kpi_kuantitatif': formula numerik tunggal
    -- 'kpi_agregat': rata-rata dari sub-indikator
    -- 'maturity_level': stream maturity level
    -- 'maturity_level_kpi': agregat ML + KPI dengan bobot
    -- 'compliance_pengurang': sub komponen compliance
    formula TEXT,                           -- string formula (untuk display & audit)
    formula_data JSONB,                     -- struktur data formula (untuk eval)
    satuan VARCHAR(20),                     -- '%', 'kg/kWh', 'Level', 'Indeks'
    target_default DECIMAL(15,4),
    periode_assessment VARCHAR(20),         -- 'semester' | 'triwulan' | 'bulanan'
    sumber_data TEXT,
    deskripsi TEXT,
    parent_indikator_id UUID REFERENCES indikator(id),  -- untuk sub-indikator
    urutan INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(perspektif_id, code)
);

-- Mapping indikator ke pemilik proses (bisa multi-bidang)
CREATE TABLE indikator_owners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indikator_id UUID NOT NULL REFERENCES indikator(id) ON DELETE CASCADE,
    bidang_id UUID NOT NULL REFERENCES bidang(id) ON DELETE CASCADE,
    role_in_process VARCHAR(50) DEFAULT 'pic',  -- 'pic' | 'reviewer' | 'co_owner'
    UNIQUE(indikator_id, bidang_id)
);

CREATE INDEX idx_indikator_perspektif ON indikator(perspektif_id);
CREATE INDEX idx_indikator_owners_bidang ON indikator_owners(bidang_id);
```

### 3.3 Struktur Maturity Level (Dynamic Schema)

```sql
-- Setiap stream maturity level (Outage, Reliability, dll) punya struktur unik
-- Disimpan sebagai dokumen JSONB
CREATE TABLE ml_stream (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indikator_id UUID NOT NULL REFERENCES indikator(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,              -- 'outage_management', 'reliability'
    name VARCHAR(255) NOT NULL,
    bobot_ml DECIMAL(5,2) NOT NULL,         -- e.g. 50 untuk Outage, 90 untuk Operation
    bobot_kpi DECIMAL(5,2) NOT NULL,        -- e.g. 50 untuk Outage, 10 untuk Operation
    structure JSONB NOT NULL,
    -- Contoh structure:
    -- {
    --   "areas": [
    --     {
    --       "code": "I1.1",
    --       "name": "Long Term Planning",
    --       "weight": 0.25,           -- bobot dalam stream (jika ada)
    --       "sub_areas": [
    --         {
    --           "code": "I1.1.1",
    --           "name": "Rencana Jangka Panjang",
    --           "uraian": "...",
    --           "criteria": {
    --             "level_0": "≤1: Fire Fighting...",
    --             "level_1": "1<x≤2: ...",
    --             "level_2": "...",
    --             "level_3": "...",
    --             "level_4": "..."
    --           }
    --         }
    --       ]
    --     }
    --   ]
    -- }
    version VARCHAR(20) DEFAULT '1.0',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(indikator_id, code)
);

CREATE INDEX idx_ml_stream_structure ON ml_stream USING GIN (structure);
```

### 3.4 Periode

```sql
CREATE TABLE periode (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES konkin_template(id),
    tahun INTEGER NOT NULL,
    triwulan INTEGER NOT NULL CHECK (triwulan IN (1,2,3,4)),
    semester INTEGER NOT NULL CHECK (semester IN (1,2)),  -- TW1+TW2=S1, TW3+TW4=S2
    
    tanggal_mulai DATE NOT NULL,
    tanggal_akhir DATE NOT NULL,
    deadline_self_assessment DATE,
    deadline_asesmen DATE,
    deadline_finalisasi DATE,
    
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- 'draft' | 'aktif' | 'self_assessment' | 'asesmen' | 'finalisasi' | 'closed'
    
    nko_calculated DECIMAL(8,4),            -- snapshot NKO terakhir terhitung
    nko_pengurang_compliance DECIMAL(6,4) DEFAULT 0,
    nko_calculated_at TIMESTAMP WITH TIME ZONE,
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, tahun, triwulan)
);

CREATE INDEX idx_periode_status ON periode(status);
CREATE INDEX idx_periode_tahun ON periode(tahun, triwulan);
```

### 3.5 Assessment Session — inti operasional

```sql
-- 1 baris per kombinasi: periode × indikator × bidang_pic
CREATE TABLE assessment_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    periode_id UUID NOT NULL REFERENCES periode(id) ON DELETE CASCADE,
    indikator_id UUID NOT NULL REFERENCES indikator(id),
    bidang_pic_id UUID NOT NULL REFERENCES bidang(id),
    
    pic_user_id UUID REFERENCES users(id),
    asesor_user_id UUID REFERENCES users(id),
    
    -- Nilai input target dari RKAU/master
    target_value DECIMAL(15,4),
    target_metadata JSONB,                  -- e.g. range bawah-atas untuk kepuasan
    
    -- Self-assessment data (struktur tergantung tipe indikator)
    self_assessment JSONB,
    -- Untuk KPI Kuantitatif:
    -- { "realisasi": 84.7, "komponen": {"AH": 2150, "EPDH": 0, ...},
    --   "pencapaian_persen": 105.51, "nilai": 6.33,
    --   "catatan_pic": "...", "link_eviden": "..." }
    --
    -- Untuk Maturity Level:
    -- { "areas": [
    --     { "code": "I1.1",
    --       "sub_areas": [
    --         { "code": "I1.1.1", "level": 3, "nilai_numerik": 3.5,
    --           "catatan": "...", "link_eviden": "..." }
    --       ] } ],
    --   "ml_average": 3.27,
    --   "kpi_component": {...},
    --   "nilai_final": 3.34 }
    
    self_assessment_status VARCHAR(20) DEFAULT 'not_started',
    -- 'not_started' | 'draft' | 'submitted' | 'returned_for_revision'
    self_assessment_submitted_at TIMESTAMP WITH TIME ZONE,
    
    -- Asesmen oleh asesor
    asesor_review JSONB,
    -- { "decision": "approve" | "override" | "request_revision",
    --   "nilai_final": 105.51,
    --   "catatan_asesor": "...",
    --   "reviewed_at": "..." }
    
    asesor_status VARCHAR(20) DEFAULT 'pending',
    -- 'pending' | 'in_review' | 'approved' | 'overridden' | 'returned'
    asesor_reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Final values setelah asesmen
    nilai_realisasi DECIMAL(15,4),
    pencapaian_persen DECIMAL(8,4),
    nilai_kontribusi DECIMAL(8,4),          -- nilai untuk perhitungan NKO
    
    locked BOOLEAN DEFAULT FALSE,           -- true setelah periode closed
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(periode_id, indikator_id, bidang_pic_id)
);

CREATE INDEX idx_assessment_periode ON assessment_session(periode_id);
CREATE INDEX idx_assessment_indikator ON assessment_session(indikator_id);
CREATE INDEX idx_assessment_pic_user ON assessment_session(pic_user_id);
CREATE INDEX idx_assessment_asesor ON assessment_session(asesor_user_id);
CREATE INDEX idx_assessment_status ON assessment_session(self_assessment_status, asesor_status);
CREATE INDEX idx_assessment_self_data ON assessment_session USING GIN (self_assessment);
```

### 3.6 Rekomendasi & Tindak Lanjut

```sql
CREATE TABLE recommendation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source: dari asesmen periode mana
    source_assessment_id UUID NOT NULL REFERENCES assessment_session(id),
    source_periode_id UUID NOT NULL REFERENCES periode(id),
    indikator_id UUID NOT NULL REFERENCES indikator(id),
    bidang_pic_id UUID NOT NULL REFERENCES bidang(id),
    
    -- Target: harus selesai di periode mana
    target_periode_id UUID REFERENCES periode(id),
    
    -- Konten
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    -- 'low' | 'medium' | 'high' | 'critical'
    deskripsi TEXT NOT NULL,
    action_items JSONB,                     -- [{action, deadline, owner_user_id}]
    target_outcome TEXT,
    
    -- Status lifecycle
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    -- 'open' | 'in_progress' | 'pending_review' | 'closed' | 'carried_over'
    
    -- Tindak lanjut
    pic_progress_notes TEXT,
    pic_completed_at TIMESTAMP WITH TIME ZONE,
    asesor_verified_at TIMESTAMP WITH TIME ZONE,
    asesor_close_notes TEXT,
    
    -- Carry-over chain
    carried_from_id UUID REFERENCES recommendation(id),
    carried_to_id UUID REFERENCES recommendation(id),
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_recommendation_status ON recommendation(status);
CREATE INDEX idx_recommendation_target_periode ON recommendation(target_periode_id);
CREATE INDEX idx_recommendation_bidang ON recommendation(bidang_pic_id);

-- Update progress per recommendation (history)
CREATE TABLE recommendation_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id UUID NOT NULL REFERENCES recommendation(id) ON DELETE CASCADE,
    progress_percent INTEGER CHECK (progress_percent BETWEEN 0 AND 100),
    notes TEXT,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.7 Compliance Tracker

```sql
CREATE TABLE compliance_laporan_definisi (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES konkin_template(id),
    code VARCHAR(50) UNIQUE NOT NULL,       -- 'LAPORAN_PENGUSAHAAN', 'BA_TRANSFER_ENERGI'
    nama VARCHAR(255) NOT NULL,
    frekuensi VARCHAR(20) NOT NULL,         -- 'bulanan' | 'triwulan' | 'semesteran' | 'harian'
    bidang_pic_id UUID REFERENCES bidang(id),
    deadline_pattern VARCHAR(50),           -- 'tanggal_5_setiap_bulan', 'H+5_closing', 'akhir_periode'
    pengurang_per_keterlambatan DECIMAL(6,4) DEFAULT 0.039,
    pengurang_per_invaliditas DECIMAL(6,4) DEFAULT 0.039,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE compliance_laporan_submission (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    laporan_definisi_id UUID NOT NULL REFERENCES compliance_laporan_definisi(id),
    periode_id UUID NOT NULL REFERENCES periode(id),
    
    deadline DATE NOT NULL,
    tanggal_submit DATE,
    tepat_waktu BOOLEAN,
    valid_data BOOLEAN DEFAULT TRUE,
    
    keterlambatan_hari INTEGER GENERATED ALWAYS AS (
        CASE WHEN tanggal_submit IS NULL THEN NULL
             WHEN tanggal_submit > deadline THEN (tanggal_submit - deadline)
             ELSE 0 END
    ) STORED,
    
    pengurang_terhitung DECIMAL(6,4) DEFAULT 0,
    notes TEXT,
    submitted_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(laporan_definisi_id, periode_id)
);

-- Komponen Compliance lain (PACA, Critical Event, ICOFR, dll)
CREATE TABLE compliance_komponen (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES konkin_template(id),
    code VARCHAR(50) NOT NULL,              -- 'PACA', 'CRITICAL_EVENT', 'ICOFR', 'NAC'
    nama VARCHAR(255) NOT NULL,
    bobot_max_pengurang DECIMAL(6,4),
    formula TEXT,
    bidang_pic_id UUID REFERENCES bidang(id),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(template_id, code)
);

CREATE TABLE compliance_komponen_realisasi (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    komponen_id UUID NOT NULL REFERENCES compliance_komponen(id),
    periode_id UUID NOT NULL REFERENCES periode(id),
    nilai_realisasi JSONB,                  -- struktur tergantung komponen
    pengurang_terhitung DECIMAL(6,4) DEFAULT 0,
    notes TEXT,
    UNIQUE(komponen_id, periode_id)
);
```

### 3.8 NKO Snapshot & Audit

```sql
-- Snapshot NKO per perhitungan (untuk tracking perubahan)
CREATE TABLE nko_snapshot (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    periode_id UUID NOT NULL REFERENCES periode(id),
    
    nilai_pilar_i DECIMAL(8,4),
    nilai_pilar_ii DECIMAL(8,4),
    nilai_pilar_iii DECIMAL(8,4),
    nilai_pilar_iv DECIMAL(8,4),
    nilai_pilar_v DECIMAL(8,4),
    nilai_pengurang DECIMAL(8,4),
    nko_total DECIMAL(8,4),
    
    breakdown JSONB,                        -- detail per indikator
    
    is_final BOOLEAN DEFAULT FALSE,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_nko_snapshot_periode ON nko_snapshot(periode_id);

-- Audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,            -- 'create', 'update', 'delete', 'submit', 'approve'
    entity_type VARCHAR(100) NOT NULL,      -- 'assessment_session', 'recommendation', etc
    entity_id UUID,
    before_data JSONB,
    after_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);
```

### 3.9 AI Assistant — Conversation & RAG

```sql
-- Conversation history (untuk chat dengan Pedoman Konkin)
CREATE TABLE ai_conversation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    context_type VARCHAR(50),               -- 'general', 'indikator_specific', 'pedoman'
    context_id UUID,                         -- e.g. indikator_id jika context_type='indikator_specific'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE ai_message (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES ai_conversation(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,              -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    metadata JSONB,                          -- token_count, model_used, latency
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RAG: Pedoman Konkin yang sudah di-chunk dan di-embed
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector

CREATE TABLE pedoman_chunk (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_doc VARCHAR(100) NOT NULL,       -- 'PEDOMAN_2025'
    section VARCHAR(255),                    -- '1.1 Economic & Social Value'
    chunk_index INTEGER,
    content TEXT NOT NULL,
    embedding vector(768),                   -- atau 1536 tergantung model
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pedoman_embedding ON pedoman_chunk USING ivfflat (embedding vector_cosine_ops);

-- AI Suggestions (audit trail untuk tahu mana yang AI-assisted)
CREATE TABLE ai_suggestion_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    suggestion_type VARCHAR(50),
    -- 'justification_draft', 'recommendation_draft', 'anomaly_alert',
    -- 'summary_generation', 'action_plan'
    context_entity_type VARCHAR(100),
    context_entity_id UUID,
    prompt TEXT,
    suggestion_text TEXT,
    accepted BOOLEAN,
    user_edited_version TEXT,
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.10 Notification

```sql
CREATE TABLE notification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    -- 'assessment_due', 'review_pending', 'recommendation_assigned',
    -- 'deadline_approaching', 'periode_closed', 'system_announcement'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link_to VARCHAR(255),                    -- internal URL
    read_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_user_unread ON notification(user_id) WHERE read_at IS NULL;
```

---

## 4. Sample Seed Data — Struktur Konkin 2026

```sql
-- Seed Konkin Template
INSERT INTO konkin_template (id, tahun, unit_code, nomor_dokumen, judul, is_active)
VALUES (
  uuid_generate_v4(),
  2026,
  'UP_TENAYAN',
  'FMZ-12.1.2.1',
  'Kontrak Kinerja PT PLN Nusantara Power Unit Pembangkitan Tenayan Tahun 2026',
  TRUE
);

-- Asumsikan template_id sudah dapat
-- Seed perspektif (insert pakai SELECT untuk dapat template_id)

WITH t AS (SELECT id FROM konkin_template WHERE tahun=2026 AND unit_code='UP_TENAYAN')
INSERT INTO perspektif (template_id, code, name, bobot, sifat, urutan)
SELECT t.id, c, n, b, s, u FROM t,
  (VALUES
    ('I',   'Economic & Social Value',     46.00, 'penambah', 1),
    ('II',  'Model Business Innovation',   25.00, 'penambah', 2),
    ('III', 'Technology Leadership',        6.00, 'penambah', 3),
    ('IV',  'Energize Investment',          8.00, 'penambah', 4),
    ('V',   'Unleash Talent',              15.00, 'penambah', 5),
    ('VI',  'Compliance',                   0.00, 'pengurang', 6)
  ) AS v(c,n,b,s,u);

-- Seed indikator level 1 (Pilar I)
WITH p AS (
  SELECT id FROM perspektif
  WHERE code='I' AND template_id IN (SELECT id FROM konkin_template WHERE tahun=2026)
)
INSERT INTO indikator (perspektif_id, code, nama, bobot, polaritas, tipe, urutan)
SELECT p.id, c, n, b, pol, t, u FROM p,
  (VALUES
    ('BPP_UNIT',           'Pengendalian Komponen BPP Unit',           18.00, 'positif', 'kpi_agregat',      1),
    ('OPT_PASOKAN',        'Optimalisasi Kesiapan Pasokan Pembangkit',  6.00, 'positif', 'kpi_kuantitatif',  2),
    ('EAF',                'EAF (Equivalent Availability Factor)',      6.00, 'positif', 'kpi_kuantitatif',  3),
    ('EFOR',               'EFOR (Equivalent Forced Outage Rate)',      6.00, 'negatif', 'kpi_kuantitatif',  4),
    ('SDGS',               'Pengelolaan Sustainable Development Goals',10.00, 'positif', 'kpi_agregat',      5)
  ) AS v(c,n,b,pol,t,u);

-- Pilar II: Maturity Level Manajemen Aset
WITH p AS (SELECT id FROM perspektif WHERE code='II' AND template_id IN (SELECT id FROM konkin_template WHERE tahun=2026))
INSERT INTO indikator (perspektif_id, code, nama, bobot, tipe, urutan)
SELECT p.id, 'ML_ASET_PEMBANGKIT', 'Maturity Level Manajemen Aset Pembangkitan', 25.00, 'maturity_level_kpi', 1
FROM p;

-- (Sub-indikator BPP, SDGs, dan stream ML akan di-seed di skrip terpisah)

-- Bidang utama PLTU Tenayan
INSERT INTO bidang (code, name) VALUES
  ('BID_OM_1', 'Bidang Operasi & Maintenance OM-1'),
  ('BID_OM_2', 'Bidang Operasi & Maintenance OM-2'),
  ('BID_OM_3', 'Bidang Operasi & Maintenance OM-3'),
  ('BID_OM_RE','Bidang Operasi & Maintenance Renewable Energy'),
  ('BID_REL_1','Bidang Reliability 1'),
  ('BID_REL_2','Bidang Reliability 2'),
  ('BID_HSE',  'Bidang Health, Safety & Environment'),
  ('BID_HTD',  'Bidang Human Talent Development'),
  ('BID_HSC',  'Bidang Human Capital Strategic'),
  ('BID_FIN',  'Bidang Finance'),
  ('BID_ACT',  'Bidang Accounting'),
  ('BID_RIS',  'Bidang Risk Management'),
  ('BID_CPF',  'Bidang Compliance'),
  ('BID_CMR',  'Bidang Customer Relationship'),
  ('BID_CSR',  'Bidang Corporate Social Responsibility'),
  ('BID_EPI_1','Bidang Energi Primer 1'),
  ('BID_AUD_1','Bidang Audit 1'),
  ('SSCM',     'Satuan Supply Chain Management'),
  ('SPRO',     'Satuan Project'),
  ('BID_AMS',  'Bidang Asset Management Strategy');

-- Roles
INSERT INTO roles (code, name, description) VALUES
  ('super_admin', 'Super Administrator', 'Full access termasuk konfigurasi sistem'),
  ('admin_unit',  'Admin Unit',          'Mengelola periode, user, master data unit'),
  ('pic_bidang',  'PIC Bidang',          'Self-assessment indikator bidangnya'),
  ('asesor',      'Asesor',              'Verifikasi dan beri nilai final'),
  ('manajer_unit','Manajer Unit',        'Approve final, dashboard eksekutif'),
  ('viewer',      'Viewer',              'Read-only');
```

---

## 5. Strategi Migrasi & Versioning

- Pakai **Alembic** untuk migrasi.
- Setiap perubahan struktur Konkin tahunan = `konkin_template` baru, **tidak overwrite** data lama.
- Field `version` di `ml_stream` untuk tracking perubahan rubrik antar tahun.
- Soft delete (`deleted_at`) untuk semua entitas yang punya history value.

---

## 6. Performance Considerations

- **GIN index** pada kolom JSONB yang sering di-query (`self_assessment`, `structure`).
- **Materialized view** untuk dashboard agregat (refresh per perubahan `assessment_session`).
- **Connection pooling** via PgBouncer (production).
- **Row-level security** untuk multi-tenant readiness (kalau nanti banyak unit).

---

**Selanjutnya:** [`04_API_SPEC.md`](04_API_SPEC.md) — REST API endpoints.
