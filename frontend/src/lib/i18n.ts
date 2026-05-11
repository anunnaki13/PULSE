/**
 * PULSE i18n — hand-rolled lookup map (RESEARCH.md: defer react-i18next 22kB bundle).
 *
 * Default locale: Bahasa Indonesia (CONSTR-i18n-default).
 * Structure-ready for English: add an `en` table mirroring `id` + language toggle later.
 *
 * Phase-1 keys exposed for Plan 07 (auth UI + master browse):
 *   app.name, app.tagline, app.taglineEn
 *   login.title, login.username, login.password, login.submit, login.wrong
 *   nav.master, nav.dashboard, nav.logout
 *   master.konkin, master.bidang, master.stream
 *   common.loading, common.save, common.cancel, common.empty, common.error
 */

const id = {
  app: {
    name: "PULSE",
    tagline: "Denyut Kinerja Pembangkit, Real-Time.",
    taglineEn: "The Heartbeat of Power Performance.",
  },
  login: {
    title: "Masuk ke PULSE",
    username: "Pengguna",
    password: "Kata Sandi",
    submit: "Masuk",
    wrong: "Pengguna atau kata sandi salah.",
  },
  nav: {
    master: "Master Data",
    dashboard: "Dasbor",
    logout: "Keluar",
  },
  master: {
    konkin: "Template Konkin 2026",
    bidang: "Master Bidang",
    stream: "Maturity Level Stream",
  },
  common: {
    loading: "Memuat…",
    save: "Simpan",
    cancel: "Batal",
    empty: "Tidak ada data.",
    error: "Terjadi kesalahan.",
  },
} as const;

type Dict = typeof id;

/**
 * Look up an i18n string by dotted path (e.g. `t("app.tagline")`).
 * Returns the path itself as a fallback so missing keys surface visibly.
 */
export const t = (path: string): string => {
  // Walk the BI dictionary by path segments; bail to the raw path on miss.
  const value = path.split(".").reduce<unknown>((node, segment) => {
    if (node && typeof node === "object" && segment in (node as Record<string, unknown>)) {
      return (node as Record<string, unknown>)[segment];
    }
    return undefined;
  }, id);
  return typeof value === "string" ? value : path;
};

export type { Dict };
