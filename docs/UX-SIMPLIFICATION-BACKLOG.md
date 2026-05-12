# PULSE UX Simplification Backlog

Status date: 2026-05-13

This backlog captures the user's feedback: PULSE looks good and has strong coverage, but the flow is currently confusing and there are too many added surfaces for a first pass.

The next phase should simplify before adding new features.

## Product Principle

Every role should see the smallest useful path first.

Advanced details, formula references, AI controls, audit trails, and master-data tools should still exist, but they should not compete with the primary daily workflow.

## Priority 1 - Simplify Navigation

Problem:

The current app exposes many useful menus at once. This makes the product feel powerful but hard to enter.

Recommended changes:

- Group `Panduan`, `Kamus Formula`, and `Alur Kerja` into one secondary `Bantuan` area.
- Keep daily workflow menus visible first.
- Move admin-only and reference-only pages away from the main operator path.
- Do not delete technical pages yet; re-home them after the simplified IA is designed.

Expected result:

The header/sidebar feels like an operating console, not a documentation index.

## Priority 2 - Role-Based Home

Problem:

Different users do different jobs, but the current first impression can feel the same for everyone.

Recommended landing pages:

| Role | First screen should emphasize |
|------|-------------------------------|
| PIC | Isi assessment, draft tersimpan, revisi diminta, rekomendasi saya |
| Asesor | Review pending, submission perlu keputusan, rekomendasi perlu verifikasi |
| Admin Unit | Periode, master data, user, compliance setup |
| Manajer Unit | NKO, pilar bermasalah, rekomendasi kritis, laporan |
| Viewer | Dashboard and read-only reports |

Expected result:

After login, the user knows what to do without reading a guide first.

## Priority 3 - Reduce Dashboard Density

Problem:

The dashboard is visually strong, but too many cards can make the meaning harder to scan.

Recommended default dashboard:

- Show NKO total.
- Show the 5 pilar summary.
- Show top 5 items needing attention.
- Show latest assessment/recommendation movement.
- Move simulator, detailed ledgers, long tables, and secondary analytics behind drill-down or `Lanjutan`.

Expected result:

The dashboard answers "how are we doing and what needs action?" in under 10 seconds.

## Priority 4 - Clarify Terminology

Problem:

Mixed terms like assessment, asesmen, self-assessment, indikator, stream, ML, HCR, OCR, and compliance can overwhelm new users.

Recommended changes:

- Prefer Bahasa Indonesia labels for common actions:
  - `Assessment` -> `Penilaian`
  - `Self Assessment` -> `Isi Penilaian`
  - `Submit` -> `Kirim ke Asesor`
  - `Review` -> `Periksa`
  - `Recommendation` -> `Rekomendasi`
- Keep technical names where they are official Konkin terms.
- Add short inline labels only where they reduce ambiguity.

Expected result:

Operators can act without translating system language in their head.

## Priority 5 - Label Dummy Data Clearly

Problem:

Dummy/demo data is useful for UAT, but it can look like real operational data.

Recommended changes:

- Add a visible `Data Dummy` badge for seeded/demo periods.
- Add a small note on dashboards and reports generated from dummy periods.
- Keep the dummy badge out of production periods.

Expected result:

The user can safely learn the system without mistaking demo values for official results.

## Priority 6 - Guided Primary CTA

Problem:

Some pages show many possible actions at the same level.

Recommended changes:

- Give each role one primary action per screen.
- Secondary actions should be smaller or behind menus.
- Use status-based empty states:
  - PIC: "Belum ada penilaian yang perlu diisi."
  - Asesor: "Tidak ada review pending."
  - Admin: "Buka periode baru untuk mulai siklus."

Expected result:

The interface points to the next operational step.

## Priority 7 - Keep Formula Detail Available, But Secondary

Problem:

Formula detail is important because each stream has different formula, unit, polarity, weight, and aggregation. But it should not dominate the daily workflow.

Recommended changes:

- Keep formula detail accessible from a help drawer or detail panel.
- Show only the formula relevant to the current indikator/stream inside the assessment screen.
- Keep full dictionary as reference, not a primary navigation destination.

Expected result:

Users get the right formula at the moment they need it.

## Suggested Next Phase

Phase 11 should be `UX Simplification Pass`.

Success criteria:

1. Main navigation is reduced or grouped.
2. Each role has a clear landing path.
3. Dashboard default view is simplified.
4. Dummy data is clearly labeled.
5. No core workflow capability is removed.
