# 05 — Frontend Architecture

> Struktur, routing, state management, dan komponen kunci aplikasi React SISKONKIN.

---

## 1. Tech Stack Frontend

| Layer | Library | Tujuan |
|------|---------|--------|
| Framework | React 18 + Vite + TypeScript | Build engine cepat, type-safe |
| Routing | React Router v6 | SPA routing |
| Server state | TanStack Query (React Query) v5 | Fetching, caching, optimistic updates |
| Client state | Zustand | UI state ringan, role context |
| Forms | React Hook Form + Zod | Form validation + type inference |
| Styling | Tailwind CSS + custom skeuomorphic tokens | Utility-first, tema khusus |
| UI Components | Custom + shadcn/ui (di-fork untuk tema skeuomorphic) | Component primitives |
| Icons | Lucide React + Heroicons | Icon set |
| Charts | Recharts atau Apache ECharts | Dashboard visualization |
| Date | date-fns + dayjs | Date manipulation |
| HTTP | Axios | API client dengan interceptor JWT |
| Real-time | native WebSocket atau Socket.IO client | Push notif, NKO update |
| Animation | Motion (framer-motion) | Transition halus |
| Toast | Sonner | Notifikasi |

---

## 2. Struktur Direktori

```
frontend/
├── public/
│   ├── fonts/                          # Custom fonts skeuomorphic
│   └── textures/                       # Brushed metal, dial, dll
├── src/
│   ├── main.tsx                        # Entry point
│   ├── App.tsx
│   ├── routes/                         # File-based routing
│   │   ├── _root.tsx
│   │   ├── login.tsx
│   │   ├── dashboard/
│   │   │   ├── index.tsx
│   │   │   └── executive.tsx
│   │   ├── self-assessment/
│   │   │   ├── index.tsx               # List indikator user
│   │   │   ├── $sessionId.tsx          # Form per indikator
│   │   │   └── components/
│   │   │       ├── KpiKuantitatifForm.tsx
│   │   │       └── MaturityLevelForm.tsx
│   │   ├── asesmen/
│   │   │   ├── index.tsx
│   │   │   └── $sessionId.tsx
│   │   ├── recommendations/
│   │   │   ├── index.tsx
│   │   │   └── $id.tsx
│   │   ├── compliance/
│   │   │   └── index.tsx
│   │   ├── periode/
│   │   ├── master/                     # Admin: master data
│   │   │   ├── konkin-template/
│   │   │   ├── indikator/
│   │   │   ├── stream-ml/
│   │   │   ├── bidang/
│   │   │   └── users/
│   │   └── ai/
│   │       └── chat.tsx
│   ├── api/                            # API client per resource
│   │   ├── client.ts                   # Axios instance + interceptors
│   │   ├── auth.ts
│   │   ├── konkin.ts
│   │   ├── periode.ts
│   │   ├── assessment.ts
│   │   ├── recommendation.ts
│   │   ├── compliance.ts
│   │   ├── nko.ts
│   │   ├── ai.ts
│   │   └── types.ts                    # TypeScript types match backend schemas
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useAssessment.ts
│   │   ├── useNkoCalculation.ts
│   │   ├── useDebounce.ts
│   │   ├── useWebSocket.ts
│   │   └── useAi.ts
│   ├── stores/
│   │   ├── authStore.ts                # Zustand: user, roles, current bidang
│   │   ├── periodeStore.ts             # Periode aktif yang dipilih user
│   │   └── uiStore.ts                  # Sidebar collapsed, modal, dll
│   ├── components/
│   │   ├── primitives/                 # Skeuomorphic primitives
│   │   │   ├── SkButton.tsx            # Tombol seperti hardware button
│   │   │   ├── SkDial.tsx              # Knob/dial bulat (untuk select level)
│   │   │   ├── SkSlider.tsx            # Slider dengan tactile feel
│   │   │   ├── SkPanel.tsx             # Panel "metal" container
│   │   │   ├── SkToggle.tsx            # Switch fisik
│   │   │   ├── SkLed.tsx               # LED indicator (status)
│   │   │   ├── SkGauge.tsx             # Analog meter (untuk persen)
│   │   │   ├── SkScreenLcd.tsx         # LCD-style display
│   │   │   ├── SkInput.tsx             # Input dengan inset shadow
│   │   │   ├── SkSelect.tsx
│   │   │   └── SkBadge.tsx
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── BreadcrumbNav.tsx
│   │   │   └── PeriodeSelector.tsx
│   │   ├── assessment/
│   │   │   ├── KpiKuantitatifForm.tsx
│   │   │   ├── MaturityLevelTree.tsx
│   │   │   ├── MaturityLevelSubAreaCard.tsx
│   │   │   ├── LevelSelector.tsx       # 5-position dial untuk level 0-4
│   │   │   ├── EvidenceLink.tsx
│   │   │   └── AssessmentStatusBadge.tsx
│   │   ├── dashboard/
│   │   │   ├── NkoGauge.tsx            # Big analog gauge NKO
│   │   │   ├── PilarPanel.tsx
│   │   │   ├── HeatmapMaturity.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   └── KpiCard.tsx
│   │   ├── recommendation/
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   └── SeverityBadge.tsx
│   │   ├── ai/
│   │   │   ├── AiAssistButton.tsx
│   │   │   ├── AiSuggestionDrawer.tsx
│   │   │   └── AiChat.tsx
│   │   └── shared/
│   │       ├── DataTable.tsx
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── lib/
│   │   ├── nko-calculator.ts           # Client-side preview perhitungan
│   │   ├── format.ts                   # Number, date, currency formatter
│   │   ├── permissions.ts              # Helper cek role/permission
│   │   ├── ml-tree-utils.ts            # Traverse, calculate average
│   │   └── constants.ts                # Level definitions, colors per level
│   ├── styles/
│   │   ├── globals.css
│   │   ├── skeuomorphic.css            # Custom CSS variables tema
│   │   └── tailwind.css
│   └── types/
│       └── index.ts
├── tailwind.config.ts                  # Custom tokens skeuomorphic
├── tsconfig.json
├── vite.config.ts
├── package.json
└── .env.example
```

---

## 3. Routing Map

```
/                            → redirect ke /dashboard atau /login
/login                       → halaman login

/dashboard                   → dashboard sesuai role
  /dashboard/executive       → eksekutif (manajer/direksi)

/self-assessment             → list sesi PIC (bidang user)
/self-assessment/:sessionId  → form (auto: KPI atau ML)

/asesmen                     → list antrian asesor
/asesmen/:sessionId          → review form

/recommendations             → list rekomendasi
/recommendations/:id         → detail + tracking

/compliance                  → tracker compliance unit
/compliance/laporan          → laporan rutin status
/compliance/komponen         → komponen compliance lain (PACA, dll)

/periode                     → list periode
/periode/:id                 → detail + summary

/master                      → (admin) master data
/master/konkin-template      → CRUD template
/master/konkin-template/:id  → editor struktur perspektif/indikator
/master/stream-ml/:id        → editor struktur maturity level (tree editor JSON)
/master/bidang
/master/users
/master/compliance-config

/ai/chat                     → AI chat dengan Pedoman
/ai/history                  → conversation history

/reports                     → laporan & export
/profile                     → user profile, change password
```

### Route Guards

```typescript
// src/lib/permissions.ts
export const requiredRoles: Record<string, Role[]> = {
  '/master/*': ['super_admin', 'admin_unit'],
  '/asesmen/*': ['asesor', 'super_admin'],
  '/dashboard/executive': ['manajer_unit', 'super_admin', 'viewer'],
  '/audit-logs': ['super_admin'],
};

// di komponen layout / loader
if (!hasAnyRole(currentUser, requiredForPath(pathname))) {
  redirect('/dashboard');
}
```

---

## 4. State Management Strategy

### Server State (TanStack Query)
Semua data dari API.

```typescript
// src/api/assessment.ts
export const useAssessmentSession = (sessionId: string) =>
  useQuery({
    queryKey: ['assessment-session', sessionId],
    queryFn: () => api.get(`/assessment/sessions/${sessionId}`),
    staleTime: 30_000,
  });

export const useUpdateSelfAssessment = () =>
  useMutation({
    mutationFn: ({ sessionId, data }) => 
      api.patch(`/assessment/sessions/${sessionId}/self-assessment`, data),
    onSuccess: (data, vars) => {
      queryClient.invalidateQueries(['assessment-session', vars.sessionId]);
    },
  });
```

### Client State (Zustand)
Hanya UI state non-server: sidebar collapsed, periode aktif yang dipilih, dll.

```typescript
// src/stores/authStore.ts
type AuthStore = {
  user: User | null;
  roles: string[];
  setUser: (u: User) => void;
  logout: () => void;
  hasRole: (r: string) => boolean;
};
```

### Form State (React Hook Form)
Untuk semua form. Validation pakai Zod schema yang bisa share dengan backend.

```typescript
const kpiSchema = z.object({
  realisasi: z.number().min(0),
  komponen: z.record(z.number()),
  catatan_pic: z.string().min(10).max(2000),
});

const form = useForm({
  resolver: zodResolver(kpiSchema),
  defaultValues: session.self_assessment ?? {},
});
```

---

## 5. Komponen Kunci — Penjelasan Detail

### 5.1 `MaturityLevelTree`

Komponen pohon area → sub-area dengan kemampuan navigasi & input level. Karena setiap stream punya struktur berbeda (dari JSONB), komponen ini sepenuhnya **data-driven**.

```tsx
type Props = {
  structure: MlStructure;            // dari ml_stream.structure
  values: MlAssessmentValues;        // current self_assessment
  onChange: (values: MlAssessmentValues) => void;
  readOnly?: boolean;
};

function MaturityLevelTree({ structure, values, onChange, readOnly }: Props) {
  return (
    <div className="space-y-4">
      {structure.areas.map(area => (
        <Accordion key={area.code}>
          <AccordionTrigger>
            <SkPanel className="flex justify-between">
              <span>{area.code} — {area.name}</span>
              <SkBadge>
                Avg {avgLevel(area, values).toFixed(2)}
              </SkBadge>
            </SkPanel>
          </AccordionTrigger>
          <AccordionContent>
            {area.sub_areas.map(sub => (
              <MaturityLevelSubAreaCard
                key={sub.code}
                subArea={sub}
                value={getValue(values, area.code, sub.code)}
                onChange={(v) => updateSubArea(area.code, sub.code, v)}
                readOnly={readOnly}
              />
            ))}
          </AccordionContent>
        </Accordion>
      ))}
    </div>
  );
}
```

### 5.2 `MaturityLevelSubAreaCard`

```tsx
function MaturityLevelSubAreaCard({ subArea, value, onChange }) {
  return (
    <SkPanel className="p-6">
      <h4 className="font-display text-lg">{subArea.name}</h4>
      <p className="text-sm text-muted">{subArea.uraian}</p>

      <LevelSelector
        levels={subArea.criteria}
        value={value?.level}
        onChange={(level) => onChange({ ...value, level })}
      />

      {value?.level !== undefined && (
        <SkSlider
          label={`Nilai numerik dalam range Level ${value.level}`}
          min={value.level === 0 ? 0 : value.level + 0.01}
          max={value.level + 1}
          step={0.01}
          value={value.nilai_numerik}
          onChange={(n) => onChange({ ...value, nilai_numerik: n })}
        />
      )}

      <SkInput
        as="textarea"
        label="Catatan"
        value={value?.catatan ?? ''}
        onChange={(e) => onChange({ ...value, catatan: e.target.value })}
      />

      <SkInput
        type="url"
        label="Link Eviden Eksternal (opsional)"
        value={value?.link_eviden ?? ''}
        onChange={(e) => onChange({ ...value, link_eviden: e.target.value })}
      />

      <AiAssistButton
        suggestionType="justification_draft"
        context={{ subArea, currentValue: value }}
        onAccept={(text) => onChange({ ...value, catatan: text })}
      />
    </SkPanel>
  );
}
```

### 5.3 `LevelSelector` (Skeuomorphic Dial)

Komponen pilihan level 0–4 sebagai **dial putar fisik** (mirip volume knob). Klik posisi atau drag untuk pilih level, dengan tooltip menampilkan kriteria deskriptif.

```tsx
function LevelSelector({ levels, value, onChange }) {
  // Dial 5 posisi: 0, 1, 2, 3, 4 dengan label deskriptif
  return (
    <div className="flex items-center gap-6">
      <SkDial 
        positions={5}
        value={value}
        onChange={onChange}
        labels={['Fire Fighting', 'Stabilizing', 'Preventing', 'Optimizing', 'Excellence']}
        accentColors={[
          'var(--sk-red)',
          'var(--sk-orange)',
          'var(--sk-yellow)',
          'var(--sk-green)',
          'var(--sk-emerald)',
        ]}
      />
      <SkScreenLcd>
        {value !== undefined ? (
          <>
            <span className="font-mono text-2xl">L{value}</span>
            <p className="text-xs">{levels[`level_${value}`]}</p>
          </>
        ) : (
          <span className="text-muted">Pilih level…</span>
        )}
      </SkScreenLcd>
    </div>
  );
}
```

### 5.4 `NkoGauge` (Dashboard Centerpiece)

Analog meter besar yang menampilkan NKO dengan jarum bergerak.

```tsx
function NkoGauge({ value, target = 100 }) {
  return (
    <div className="relative w-96 h-96">
      {/* SVG analog gauge dengan needle berputar */}
      <svg viewBox="0 0 200 200">
        {/* arc background */}
        {/* tick marks */}
        {/* color zones (red < 80, yellow 80-100, green 100+) */}
        {/* needle */}
        <g transform={`rotate(${calcAngle(value, 0, 120)} 100 100)`}>
          <line x1="100" y1="100" x2="100" y2="20" stroke="..." />
        </g>
        {/* center cap */}
      </svg>
      <SkScreenLcd className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <span className="font-mono text-4xl">{value.toFixed(2)}</span>
        <span className="text-xs">/ {target}</span>
      </SkScreenLcd>
    </div>
  );
}
```

### 5.5 `AiAssistButton` & `AiSuggestionDrawer`

Tombol AI muncul di tempat-tempat strategis (catatan PIC, draf rekomendasi). Klik → drawer dari kanan dengan loading state, lalu menampilkan suggestion. User bisa **Accept**, **Edit**, atau **Discard**.

```tsx
function AiAssistButton({ suggestionType, context, onAccept }) {
  const [open, setOpen] = useState(false);
  const { mutate, data, isPending } = useAiSuggestion(suggestionType);

  return (
    <>
      <SkButton variant="accent" icon={<Sparkles />} onClick={() => {
        setOpen(true);
        mutate(context);
      }}>
        AI Assist
      </SkButton>
      
      <AiSuggestionDrawer
        open={open}
        loading={isPending}
        suggestion={data?.suggestion}
        onAccept={(finalText) => { onAccept(finalText); setOpen(false); }}
        onClose={() => setOpen(false)}
      />
    </>
  );
}
```

---

## 6. Performance Patterns

### Code Splitting
- Route-based code splitting via `React.lazy`
- Heavy charts library di-lazy
- Master data editor di-lazy (jarang dipakai PIC biasa)

### Optimistic Updates
- Save draft self-assessment: optimistic
- Mark recommendation progress: optimistic
- Reject pada error → rollback dengan toast

### Auto-save
- Self-assessment form auto-save tiap 5 detik (debounced) ke endpoint `PATCH /sessions/{id}/self-assessment`
- Status `Saved 2s ago` ditampilkan di pojok form

### Real-time Updates
- WebSocket subscribe ke `/ws/dashboard` saat di dashboard untuk auto-update NKO
- Subscribe ke `/ws/notifications` saat login

---

## 7. Accessibility

- Semantic HTML (form labels, ARIA roles)
- Keyboard navigation untuk semua skeuomorphic component (dial: arrow keys)
- Focus indicator visible
- Color contrast ≥ AA (skeuomorphic ≠ low contrast)
- Screen reader: aria-describedby untuk kriteria level

---

## 8. i18n

Semua copy dalam **Bahasa Indonesia** (default). Persiapkan struktur untuk dukungan English nanti:

```typescript
// src/i18n/id.ts
export const id = {
  assessment: {
    submit: 'Submit untuk Asesmen',
    save_draft: 'Simpan Draft',
    realisasi: 'Realisasi',
    target: 'Target',
    pencapaian: 'Pencapaian',
    nilai_kontribusi: 'Nilai Kontribusi',
  },
  // ...
};
```

Pakai `react-intl` atau simple object lookup untuk MVP.

---

## 9. Build & Environment

### Environment Variables
```
VITE_API_BASE_URL=https://siskonkin.tenayan.local/api/v1
VITE_WS_BASE_URL=wss://siskonkin.tenayan.local/ws
VITE_APP_VERSION=1.0.0
VITE_SENTRY_DSN=...                # opsional
```

### Build
```bash
pnpm build                          # output ke dist/
docker build -t siskonkin-frontend .
```

### Production Hosting
- Static files di-serve oleh Nginx (lihat `08_DEPLOYMENT.md`)
- Cache headers untuk asset (immutable hashed filenames)

---

**Selanjutnya:** [`06_DESIGN_SYSTEM_SKEUOMORPHIC.md`](06_DESIGN_SYSTEM_SKEUOMORPHIC.md) — sistem desain skeuomorphic.
