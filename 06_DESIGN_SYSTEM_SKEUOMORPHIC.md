# 06 — Design System: Skeuomorphic Control Room

> Sistem desain SISKONKIN yang mengambil inspirasi dari **panel kontrol pembangkit listrik** dan **instrumen analog tradisional** — diterjemahkan ke web modern dengan teknik skeuomorphic & neumorphic.

---

## 1. Filosofi Desain

PLTU Tenayan adalah dunia mesin, instrumen, dial pengukur, indikator LED, panel kontrol logam. UI SISKONKIN dirancang **bukan** sebagai dashboard SaaS generik, tapi sebagai **control room digital** — di mana pengukuran kinerja terasa seperti membaca instrumen real, dan input data terasa seperti memutar tuas atau menekan tombol.

Tiga pilar:

1. **Tactile** — semua elemen interaktif punya respons fisik visual (tekan masuk, knob berputar, slider gesekan).
2. **Industrial Refinement** — bukan retro/playful, tapi serius dan presisi seperti instrumen lab/industri.
3. **Information First** — meskipun kaya tekstur, hierarki informasi tetap jelas. Decoration tidak mengalahkan fungsi.

### Inspirasi Visual
Mengacu pada gambar yang Anda upload:
- **Neumorphic cards** dengan inset/outset shadow (Image 4 — kartu HRTBT dan statistik)
- **Frosted glass + dial besar** dengan tactile knob (Image 3 — Radio Player) 
- **Light surfaces dengan precision typography** (Image 2 — temperature dial 26°C)
- **Layered widgets** berdiri di atas surface gelap dengan depth (Image 1 — clock widgets)

Direkonstruksi dengan tema **PLN Industrial**: dominan navy/dark steel + aksen kuning PLN + LCD green untuk display, mengingatkan pada control room thermal power plant.

---

## 2. Design Tokens

### 2.1 Warna

```css
:root {
  /* === SURFACE — Material Logam & Kaca === */
  --sk-surface-base:        #1a1f2e;   /* dark steel, untuk page background */
  --sk-surface-raised:      #232938;   /* panel terangkat */
  --sk-surface-deep:        #0f1218;   /* recessed area, screen background */
  --sk-surface-lcd:         #0a1410;   /* LCD background green-tint */
  --sk-surface-light:       #f4f1ea;   /* untuk light theme variant: panel cream */
  --sk-surface-light-deep:  #e5e0d4;   /* recessed di light theme */

  /* === BORDERS & DIVIDERS === */
  --sk-border-subtle:       #2d3447;
  --sk-border-emphasis:     #3d4663;
  --sk-bezel-light:         rgba(255, 255, 255, 0.08);  /* highlight rim */
  --sk-bezel-dark:          rgba(0, 0, 0, 0.45);        /* shadow rim */

  /* === BRAND PLN === */
  --sk-pln-blue:            #1e3a8a;   /* logo blue */
  --sk-pln-blue-bright:     #3b82f6;
  --sk-pln-yellow:          #fbbf24;   /* accent */
  --sk-pln-yellow-glow:     #fde047;

  /* === SEMANTIC LEVEL COLORS === */
  --sk-level-0:             #ef4444;   /* Fire Fighting — red */
  --sk-level-1:             #f97316;   /* Stabilizing — orange */
  --sk-level-2:             #eab308;   /* Preventing — yellow */
  --sk-level-3:             #22c55e;   /* Optimizing — green */
  --sk-level-4:             #10b981;   /* Excellence — emerald */

  /* === SEMANTIC STATUS === */
  --sk-success:             #10b981;
  --sk-warning:             #f59e0b;
  --sk-danger:              #ef4444;
  --sk-info:                #3b82f6;

  /* === LCD / SCREEN COLORS === */
  --sk-lcd-text:            #4ade80;   /* phosphor green */
  --sk-lcd-text-amber:      #fbbf24;
  --sk-lcd-glow:            0 0 8px rgba(74, 222, 128, 0.55);

  /* === TEXT === */
  --sk-text-primary:        #e7eaf2;
  --sk-text-secondary:      #a1a8bd;
  --sk-text-muted:          #6b7280;
  --sk-text-on-light:       #1a1f2e;

  /* === LED INDICATOR === */
  --sk-led-on-green:        #10b981;
  --sk-led-on-red:          #ef4444;
  --sk-led-on-amber:        #f59e0b;
  --sk-led-off:             #2d3447;
}
```

### 2.2 Tipografi

Pemilihan font harus sengaja, memperkuat karakter "instrumen industri":

```css
/* Display & Heading: industrial geometric */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&display=swap');

/* Body & UI: clean industrial sans (bukan Inter, bukan Roboto) */
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&display=swap');

/* Mono: untuk LCD display, angka, kode */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');  /* terminal style */

/* Optional: 7-segment LCD font untuk gauge values */
/* Pakai 'DSEG7' atau 'Digital-7' jika mau ekstra autentik */

:root {
  --font-display:  'Bebas Neue', 'Oswald', sans-serif;     /* big numbers, headers */
  --font-heading:  'Oswald', sans-serif;
  --font-body:     'Barlow', system-ui, sans-serif;
  --font-mono:     'JetBrains Mono', monospace;
  --font-lcd:      'Share Tech Mono', 'DSEG7', monospace;
}

/* Type scale */
:root {
  --text-xs:    0.75rem;     /* 12px */
  --text-sm:    0.875rem;    /* 14px */
  --text-base:  1rem;        /* 16px */
  --text-lg:    1.125rem;    /* 18px */
  --text-xl:    1.25rem;     /* 20px */
  --text-2xl:   1.5rem;      /* 24px */
  --text-3xl:   1.875rem;    /* 30px */
  --text-4xl:   2.25rem;     /* 36px */
  --text-5xl:   3rem;        /* 48px — gauge values */
  --text-6xl:   3.75rem;     /* 60px — NKO main display */
}
```

### 2.3 Spacing & Sizing

```css
:root {
  --space-1:    0.25rem;
  --space-2:    0.5rem;
  --space-3:    0.75rem;
  --space-4:    1rem;
  --space-6:    1.5rem;
  --space-8:    2rem;
  --space-12:   3rem;
  --space-16:   4rem;

  /* Bezel/border thickness */
  --bezel-thin:    1px;
  --bezel-normal:  2px;
  --bezel-thick:   3px;

  /* Border radius */
  --radius-sm:    4px;
  --radius-md:    8px;
  --radius-lg:    12px;
  --radius-xl:    16px;
  --radius-2xl:   24px;
  --radius-full:  9999px;
}
```

### 2.4 Shadow System (Inti Skeuomorphic)

```css
:root {
  /* === RAISED (mengangkat dari surface) === */
  --shadow-raised-sm:
    0 1px 2px rgba(0, 0, 0, 0.4),
    0 1px 1px rgba(255, 255, 255, 0.04) inset;

  --shadow-raised-md:
    0 4px 8px rgba(0, 0, 0, 0.5),
    0 2px 4px rgba(0, 0, 0, 0.3),
    0 1px 0 rgba(255, 255, 255, 0.06) inset,
    0 -1px 0 rgba(0, 0, 0, 0.3) inset;

  --shadow-raised-lg:
    0 12px 24px rgba(0, 0, 0, 0.5),
    0 6px 12px rgba(0, 0, 0, 0.35),
    0 1px 0 rgba(255, 255, 255, 0.08) inset,
    0 -1px 0 rgba(0, 0, 0, 0.4) inset;

  /* === RECESSED (tertanam ke surface, untuk input/screen) === */
  --shadow-recessed-sm:
    0 1px 2px rgba(0, 0, 0, 0.5) inset,
    0 -1px 0 rgba(255, 255, 255, 0.05) inset;

  --shadow-recessed-md:
    0 3px 6px rgba(0, 0, 0, 0.55) inset,
    0 1px 2px rgba(0, 0, 0, 0.7) inset,
    0 -1px 0 rgba(255, 255, 255, 0.06) inset;

  --shadow-recessed-lg:
    0 6px 12px rgba(0, 0, 0, 0.65) inset,
    0 2px 4px rgba(0, 0, 0, 0.85) inset,
    0 -1px 0 rgba(255, 255, 255, 0.08) inset;

  /* === PRESSED (tombol ditekan) === */
  --shadow-pressed:
    0 1px 2px rgba(0, 0, 0, 0.6) inset,
    0 -1px 1px rgba(255, 255, 255, 0.04) inset;

  /* === BEZEL (rim metal di sekitar component) === */
  --shadow-bezel:
    0 0 0 1px var(--sk-bezel-dark),
    0 0 0 2px var(--sk-border-subtle),
    0 0 0 3px var(--sk-bezel-light);
}
```

### 2.5 Transitions

```css
:root {
  --ease-tactile:  cubic-bezier(0.34, 1.56, 0.64, 1);   /* sedikit overshoot, tactile */
  --ease-smooth:   cubic-bezier(0.4, 0, 0.2, 1);
  --ease-snappy:   cubic-bezier(0.5, 0, 0.5, 1);

  --duration-fast:    120ms;
  --duration-normal:  200ms;
  --duration-slow:    400ms;
}
```

---

## 3. Komponen Skeuomorphic

### 3.1 SkPanel — Container Dasar

```css
.sk-panel {
  background: linear-gradient(
    180deg,
    var(--sk-surface-raised) 0%,
    color-mix(in srgb, var(--sk-surface-raised) 90%, black) 100%
  );
  border: 1px solid var(--sk-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-raised-md);
  position: relative;
}

/* Highlight rim atas */
.sk-panel::before {
  content: '';
  position: absolute;
  inset: 1px 1px auto 1px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.15) 50%,
    transparent
  );
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.sk-panel--recessed {
  background: var(--sk-surface-deep);
  box-shadow: var(--shadow-recessed-md);
}
```

### 3.2 SkButton

```css
.sk-button {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--sk-pln-blue-bright) 100%, white 8%) 0%,
    var(--sk-pln-blue) 100%
  );
  color: white;
  border: 1px solid color-mix(in srgb, var(--sk-pln-blue) 100%, black 25%);
  border-radius: var(--radius-md);
  padding: 10px 24px;
  font-family: var(--font-heading);
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: var(--text-sm);
  box-shadow: var(--shadow-raised-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-tactile);
  position: relative;
}

.sk-button::before {
  content: '';
  position: absolute;
  inset: 1px 1px 50% 1px;
  background: linear-gradient(180deg, rgba(255,255,255,0.15), transparent);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  pointer-events: none;
}

.sk-button:hover {
  filter: brightness(1.08);
  box-shadow: var(--shadow-raised-lg);
}

.sk-button:active {
  transform: translateY(1px);
  box-shadow: var(--shadow-pressed);
  filter: brightness(0.92);
}

.sk-button[data-variant="accent"] {
  background: linear-gradient(180deg, var(--sk-pln-yellow-glow), var(--sk-pln-yellow));
  color: var(--sk-text-on-light);
  border-color: color-mix(in srgb, var(--sk-pln-yellow) 100%, black 25%);
}

.sk-button[data-variant="ghost"] {
  background: transparent;
  border: 1px solid var(--sk-border-emphasis);
  color: var(--sk-text-primary);
  box-shadow: none;
}
```

### 3.3 SkInput (Recessed)

```css
.sk-input {
  background: var(--sk-surface-deep);
  border: 1px solid var(--sk-border-subtle);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  color: var(--sk-text-primary);
  font-family: var(--font-mono);
  box-shadow: var(--shadow-recessed-sm);
  transition: all var(--duration-fast) var(--ease-smooth);
}

.sk-input:focus {
  outline: none;
  border-color: var(--sk-pln-yellow);
  box-shadow: 
    var(--shadow-recessed-sm),
    0 0 0 3px color-mix(in srgb, var(--sk-pln-yellow) 100%, transparent 70%);
}
```

### 3.4 SkScreenLcd

```css
.sk-screen-lcd {
  background: var(--sk-surface-lcd);
  background-image: 
    linear-gradient(180deg, rgba(0, 0, 0, 0.4), transparent 30%, transparent 70%, rgba(0, 0, 0, 0.5)),
    repeating-linear-gradient(
      0deg,
      transparent 0px,
      transparent 2px,
      rgba(0, 0, 0, 0.15) 2px,
      rgba(0, 0, 0, 0.15) 3px
    );  /* scanline subtle */
  border: 1px solid #050a08;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  color: var(--sk-lcd-text);
  font-family: var(--font-lcd);
  text-shadow: var(--sk-lcd-glow);
  box-shadow: 
    var(--shadow-recessed-md),
    0 0 0 2px var(--sk-bezel-dark);
}

/* Variant amber/orange untuk warning state */
.sk-screen-lcd[data-tone="amber"] {
  color: var(--sk-lcd-text-amber);
  text-shadow: 0 0 8px rgba(251, 191, 36, 0.5);
}
```

### 3.5 SkDial (Knob Putar)

Komponen utama yang **paling memorable**.

```css
.sk-dial {
  width: 120px;
  height: 120px;
  border-radius: var(--radius-full);
  background: 
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.2), transparent 60%),
    conic-gradient(
      from 90deg,
      #4a5572 0%, #2d3447 25%, #4a5572 50%, #2d3447 75%, #4a5572 100%
    );  /* brushed metal effect */
  border: 2px solid var(--sk-border-emphasis);
  box-shadow: 
    var(--shadow-raised-lg),
    inset 0 0 0 4px color-mix(in srgb, var(--sk-surface-raised) 100%, black 15%),
    inset 0 4px 8px rgba(0, 0, 0, 0.4);
  position: relative;
  cursor: grab;
  transition: transform var(--duration-normal) var(--ease-tactile);
}

.sk-dial::before {
  /* Pointer indicator */
  content: '';
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 16px;
  background: var(--sk-pln-yellow);
  border-radius: 2px;
  box-shadow: 0 0 8px var(--sk-pln-yellow-glow);
}

.sk-dial:active {
  cursor: grabbing;
  transform: scale(0.98);
}
```

Implementasi React: pakai `framer-motion` untuk drag rotation, atau library seperti `react-dial-knob`.

### 3.6 SkLed (Indicator)

```css
.sk-led {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  background: var(--sk-led-off);
  box-shadow: 
    0 0 0 1px rgba(0, 0, 0, 0.6),
    inset 0 1px 2px rgba(0, 0, 0, 0.6);
  display: inline-block;
  position: relative;
}

.sk-led[data-state="on"][data-color="green"] {
  background: var(--sk-led-on-green);
  box-shadow: 
    0 0 0 1px rgba(0, 0, 0, 0.6),
    inset 0 1px 2px rgba(255, 255, 255, 0.3),
    0 0 8px var(--sk-led-on-green),
    0 0 16px color-mix(in srgb, var(--sk-led-on-green) 100%, transparent 50%);
  animation: led-pulse 2s ease-in-out infinite;
}

@keyframes led-pulse {
  0%, 100% { filter: brightness(1); }
  50%       { filter: brightness(1.15); }
}
```

### 3.7 SkGauge (Analog Meter)

SVG-based, untuk menampilkan persen pencapaian sebagai meter analog.

```tsx
function SkGauge({ value, max = 200, unit = '%', label }) {
  const angle = (value / max) * 240 - 120;  // -120 to +120 degrees
  
  return (
    <svg viewBox="0 0 200 130">
      <defs>
        <linearGradient id="gauge-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3d4663" />
          <stop offset="1" stopColor="#1a1f2e" />
        </linearGradient>
      </defs>
      
      {/* Bezel rim */}
      <circle cx="100" cy="100" r="90" fill="url(#gauge-bg)" />
      
      {/* Arc background */}
      <path d="M 25 100 A 75 75 0 0 1 175 100" 
            fill="none" stroke="#0f1218" strokeWidth="14" />
      
      {/* Color zones */}
      <path d="M 25 100 A 75 75 0 0 1 70 35"  
            fill="none" stroke="var(--sk-danger)" strokeWidth="10" />
      <path d="M 70 35 A 75 75 0 0 1 130 35"
            fill="none" stroke="var(--sk-warning)" strokeWidth="10" />
      <path d="M 130 35 A 75 75 0 0 1 175 100"
            fill="none" stroke="var(--sk-success)" strokeWidth="10" />
      
      {/* Tick marks */}
      {[...Array(11)].map((_, i) => {
        const tickAngle = (i / 10) * 240 - 120;
        return <Tick key={i} angle={tickAngle} />;
      })}
      
      {/* Needle */}
      <g transform={`rotate(${angle} 100 100)`}>
        <line x1="100" y1="100" x2="100" y2="30" 
              stroke="var(--sk-pln-yellow)" strokeWidth="3" 
              filter="drop-shadow(0 0 4px var(--sk-pln-yellow-glow))" />
        <circle cx="100" cy="100" r="6" fill="#1a1f2e" stroke="var(--sk-pln-yellow)" />
      </g>
      
      {/* Center cap with screw */}
      <circle cx="100" cy="100" r="10" fill="#3d4663" />
      <circle cx="100" cy="100" r="3" fill="#0f1218" />
    </svg>
  );
}
```

### 3.8 SkSlider

Slider horizontal dengan track recessed dan thumb fisik.

```css
.sk-slider-track {
  height: 8px;
  background: var(--sk-surface-deep);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-recessed-sm);
  position: relative;
}

.sk-slider-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--sk-pln-blue-bright), var(--sk-pln-yellow));
  border-radius: var(--radius-full);
  box-shadow: 0 0 8px var(--sk-pln-yellow-glow);
}

.sk-slider-thumb {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: radial-gradient(circle at 30% 30%, #5a6480, #1a1f2e);
  border: 1px solid #0f1218;
  box-shadow: 
    var(--shadow-raised-md),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  cursor: grab;
}
```

### 3.9 Level Color System

Untuk konteks Maturity Level, tiap level harus visually distinct:

```css
.level-badge[data-level="0"] { background: var(--sk-level-0); }   /* red */
.level-badge[data-level="1"] { background: var(--sk-level-1); }   /* orange */
.level-badge[data-level="2"] { background: var(--sk-level-2); }   /* yellow */
.level-badge[data-level="3"] { background: var(--sk-level-3); }   /* green */
.level-badge[data-level="4"] { background: var(--sk-level-4); }   /* emerald */
```

---

## 4. Layout Patterns

### 4.1 Dashboard Grid

```
┌─────────────────────────────────────────────────────────┐
│ [Logo PLN] SISKONKIN          [Periode▼] [User▼] [LED]  │  ← Top bar
├──────────┬──────────────────────────────────────────────┤
│          │  ┌──────────────────────┐                    │
│ Sidebar  │  │  ◯ NKO 102.45      │   [Pilar Cards x5] │
│ icon     │  │   Big Gauge          │                    │
│ +text    │  └──────────────────────┘                    │
│          │                                              │
│          │  Heatmap Maturity         Trend Chart        │
│          │                                              │
│          │  Top Performers   Needs Attention    Actions │
└──────────┴──────────────────────────────────────────────┘
```

### 4.2 Self-Assessment Form Layout

Form **panel-style** dengan area-area terlihat seperti modul instrumen yang dapat dilipat (collapsible).

### 4.3 Sidebar Navigation

```css
.sk-sidebar {
  width: 240px;
  background: var(--sk-surface-deep);
  border-right: 1px solid var(--sk-border-subtle);
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.4);
}

.sk-sidebar-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-left: 3px solid transparent;
  color: var(--sk-text-secondary);
  transition: all var(--duration-fast);
}

.sk-sidebar-item:hover {
  background: var(--sk-surface-raised);
  color: var(--sk-text-primary);
}

.sk-sidebar-item[data-active="true"] {
  background: var(--sk-surface-raised);
  border-left-color: var(--sk-pln-yellow);
  color: var(--sk-pln-yellow);
  box-shadow: inset 0 0 20px rgba(251, 191, 36, 0.08);
}
```

---

## 5. Tema Light Variant (Optional)

Untuk mengakomodasi preferensi user, sediakan light variant yang tetap mempertahankan karakter skeuomorphic — terinspirasi gambar Image 2 (white architecture dashboard) dan Image 4 (cream cards).

Light variant mengganti `--sk-surface-base` dari dark steel jadi **cream/ivory**, panel jadi off-white dengan shadow yang lebih lembut. LCD tetap dark green (untuk konsistensi metaphor).

---

## 6. Animation Patterns

### 6.1 Page Transition
- Fade + slight Y translate (15px) saat berpindah route
- Stagger reveal untuk kartu di dashboard (50ms delay per kartu)

### 6.2 NKO Gauge Update
- Needle bergerak dengan ease-tactile (overshoot)
- Sound effect "click" (opsional, bisa disable)

### 6.3 Level Selection
- Dial rotate dengan ease-tactile saat klik posisi
- LCD update dengan flicker brief

### 6.4 LED States
- Pulse subtle saat indikator status aktif
- Quick flash saat action sukses (bukan toast — LED-style feedback)

### 6.5 Form Save Indicator
- Tiga LED kecil: idle (off) → saving (amber pulse) → saved (green steady)

---

## 7. Iconography

Pakai **Lucide React** untuk konsistensi, tapi bias terhadap icon yang feel-nya teknikal/instrumen:
- `Gauge` untuk dashboard NKO
- `Activity` untuk monitoring
- `Settings2`, `Sliders` untuk config
- `LineChart`, `BarChart3` untuk analytics
- `AlertTriangle`, `AlertCircle` untuk warning
- `CheckCircle2`, `XCircle` untuk status

Hindari icon "round/cute" — pilih versi sharp.

---

## 8. Responsiveness

- **Desktop first** — aplikasi ini primary digunakan di desktop control room/office
- Tablet: layout tetap 2-column tapi sidebar collapsed by default
- Mobile (≥640px): single column, bottom nav, simplified gauge (compact mode)

Tidak prioritas mobile karena context use primarily desktop.

---

## 9. Sample Component Showcase (untuk dijadikan referensi visual saat dev)

```html
<!-- Mini Demo: NKO Card -->
<div class="sk-panel" style="padding: 24px; max-width: 400px;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <span class="font-heading uppercase tracking-wider text-secondary">
      NKO Realtime
    </span>
    <span class="sk-led" data-state="on" data-color="green"></span>
  </div>

  <div class="sk-screen-lcd" style="text-align: center; padding: 20px;">
    <span style="font-family: var(--font-lcd); font-size: 4rem;">
      102.45
    </span>
    <div style="font-size: 0.75rem; color: var(--sk-lcd-text-amber);">
      / TARGET 100.00
    </div>
  </div>

  <div style="display: flex; gap: 8px; margin-top: 16px;">
    <button class="sk-button" data-variant="accent">
      Refresh
    </button>
    <button class="sk-button" data-variant="ghost">
      Detail
    </button>
  </div>
</div>
```

---

## 10. Tailwind Config Mapping

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        sk: {
          surface: {
            base: 'var(--sk-surface-base)',
            raised: 'var(--sk-surface-raised)',
            deep: 'var(--sk-surface-deep)',
            lcd: 'var(--sk-surface-lcd)',
          },
          pln: {
            blue: 'var(--sk-pln-blue)',
            yellow: 'var(--sk-pln-yellow)',
          },
          level: {
            0: 'var(--sk-level-0)',
            1: 'var(--sk-level-1)',
            2: 'var(--sk-level-2)',
            3: 'var(--sk-level-3)',
            4: 'var(--sk-level-4)',
          },
        },
      },
      fontFamily: {
        display: 'var(--font-display)',
        heading: 'var(--font-heading)',
        body: 'var(--font-body)',
        mono: 'var(--font-mono)',
        lcd: 'var(--font-lcd)',
      },
      boxShadow: {
        'raised-md': 'var(--shadow-raised-md)',
        'raised-lg': 'var(--shadow-raised-lg)',
        'recessed-md': 'var(--shadow-recessed-md)',
        'recessed-lg': 'var(--shadow-recessed-lg)',
        'pressed': 'var(--shadow-pressed)',
      },
    },
  },
};
```

---

## 11. Don't List

Hindari hal-hal berikut yang akan merusak karakter skeuomorphic:
- ❌ Font generik (Inter, Roboto, Arial)
- ❌ Drop shadow yang terlalu lembut/blur (Material Design feel)
- ❌ Gradient ungu-pink (cliché AI/SaaS look)
- ❌ Border radius bulat berlebihan (>16px untuk button)
- ❌ Flat icon dengan thin stroke (gunakan medium stroke)
- ❌ Outline button tanpa karakter
- ❌ Animation yang terlalu cepat (<100ms — terasa cheap)
- ❌ Background putih murni untuk panel (gunakan tinted)

---

**Selanjutnya:** [`07_AI_INTEGRATION.md`](07_AI_INTEGRATION.md) — strategi integrasi AI/LLM.
