---
status: planned
phase: 06-stream-coverage-hcr-golive
plan: 02
requirements_addressed:
  - REQ-prod-checklist
---

# Plan 06-02 - HCR OCR Assessment Coverage

## Objective

Implement HCR and OCR assessment coverage using the same dynamic maturity workflow, including OCR's special OWM weighting.

## Scope

- Seed HCR areas:
  - Strategic Workforce Planning
  - Talent Acquisition
  - Talent Management & Development
  - Performance Management
  - Reward & Recognition
  - Industrial Relation
  - HC Operations
- Seed OCR six sub-areas, including OWM with 55/45 weighting.
- Add/verify calculator normalization for HCR/OCR/Pra Karya missing components.
- Ensure BID HTD and HSC applicability mapping is available for HCR/OCR.

## Verification

- Unit tests for HCR/OCR normalization and OWM weighting.
- API smoke: generated assessment sessions include at least one HCR area and all OCR sub-areas.
- Browser smoke: PIC can complete HCR/OCR self-assessment and asesor can approve.
