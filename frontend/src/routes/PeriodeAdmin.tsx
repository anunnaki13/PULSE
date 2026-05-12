import { useMemo, useState } from "react";
import { SkBadge, SkButton, SkInput, SkPanel, SkSelect } from "@/components/skeuomorphic";
import {
  type PeriodeStatus,
  statusTone,
  useCreatePeriode,
  usePeriodeList,
  useTransitionPeriode,
} from "@/lib/phase2-api";

const transitions: Record<PeriodeStatus, { target: PeriodeStatus; label: string }[]> = {
  draft: [{ target: "aktif", label: "Buka Periode" }],
  aktif: [{ target: "self_assessment", label: "Mulai Self-Assessment" }],
  self_assessment: [{ target: "asesmen", label: "Tutup Self-Assessment" }],
  asesmen: [{ target: "finalisasi", label: "Finalisasi" }],
  finalisasi: [{ target: "closed", label: "Tutup Periode" }],
  closed: [
    { target: "finalisasi", label: "Reopen ke Finalisasi" },
    { target: "asesmen", label: "Reopen ke Asesmen" },
    { target: "self_assessment", label: "Reopen ke Self-Assessment" },
  ],
};

export default function PeriodeAdmin() {
  const periode = usePeriodeList();
  const createPeriode = useCreatePeriode();
  const transitionPeriode = useTransitionPeriode();
  const rows = periode.data?.data ?? [];
  const [tahun, setTahun] = useState("2026");
  const [triwulan, setTriwulan] = useState("2");
  const [nama, setNama] = useState("TW2 2026");
  const [reason, setReason] = useState("");

  const semester = useMemo(() => (Number(triwulan) <= 2 ? 1 : 2), [triwulan]);

  async function handleCreate() {
    await createPeriode.mutateAsync({
      tahun: Number(tahun),
      triwulan: Number(triwulan),
      semester,
      nama,
      tanggal_buka: null,
      tanggal_tutup: null,
    });
  }

  return (
    <main style={{ padding: "1.5rem", display: "grid", gap: "1rem" }}>
      <section style={{ display: "grid", gridTemplateColumns: "minmax(280px, 420px) 1fr", gap: "1rem" }}>
        <SkPanel title="Buat Periode">
          <div style={{ display: "grid", gap: "0.75rem" }}>
            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Tahun</span>
              <SkInput label="Tahun" value={tahun} onChange={(e) => setTahun(e.target.value)} />
            </label>
            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Triwulan</span>
              <SkSelect label="Triwulan" value={triwulan} onChange={(e) => setTriwulan(e.target.value)}>
                <option value="1">TW1</option>
                <option value="2">TW2</option>
                <option value="3">TW3</option>
                <option value="4">TW4</option>
              </SkSelect>
            </label>
            <label style={{ display: "grid", gap: "0.35rem" }}>
              <span>Nama</span>
              <SkInput label="Nama periode" value={nama} onChange={(e) => setNama(e.target.value)} />
            </label>
            <SkBadge tone="info">Semester {semester}</SkBadge>
            <SkButton onClick={handleCreate} disabled={createPeriode.isPending}>
              {createPeriode.isPending ? "Menyimpan..." : "Buat Periode"}
            </SkButton>
          </div>
        </SkPanel>

        <SkPanel title="Catatan Rollback">
          <div style={{ display: "grid", gap: "0.75rem" }}>
            <p style={{ margin: 0, color: "var(--sk-text-mid)" }}>
              Isi alasan sebelum memakai tombol reopen periode closed. Transisi normal tidak memerlukan alasan.
            </p>
            <SkInput
              label="Alasan rollback"
              placeholder="Minimal 20 karakter untuk rollback"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>
        </SkPanel>
      </section>

      <SkPanel title="Lifecycle Periode" style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", minWidth: 920, borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--sk-text-mid)" }}>
              <th style={{ padding: "0.5rem" }}>Periode</th>
              <th style={{ padding: "0.5rem" }}>Status</th>
              <th style={{ padding: "0.5rem" }}>Update</th>
              <th style={{ padding: "0.5rem" }}>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} style={{ borderTop: "1px solid var(--sk-bevel-dark)" }}>
                <td style={{ padding: "0.5rem" }}>
                  <strong>{row.nama}</strong>
                  <div style={{ color: "var(--sk-text-mid)", fontSize: "0.85rem" }}>
                    {row.tahun} TW{row.triwulan} Semester {row.semester}
                  </div>
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <SkBadge tone={statusTone(row.status)}>{row.status}</SkBadge>
                </td>
                <td style={{ padding: "0.5rem", color: "var(--sk-text-mid)" }}>
                  {new Date(row.updated_at).toLocaleString("id-ID")}
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {transitions[row.status].map((action) => (
                      <SkButton
                        key={action.target}
                        variant={action.target === "closed" ? "primary" : "secondary"}
                        disabled={transitionPeriode.isPending}
                        onClick={() =>
                          transitionPeriode.mutate({
                            id: row.id,
                            target_state: action.target,
                            reason: row.status === "closed" ? reason : undefined,
                          })
                        }
                      >
                        {action.label}
                      </SkButton>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} style={{ padding: "1rem", color: "var(--sk-text-mid)" }}>
                  Belum ada periode. Buat TW2 2026 untuk mulai workflow assessment.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </SkPanel>
    </main>
  );
}
