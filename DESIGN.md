# Design System & Direction: DataCo Supply Chain Intelligence

> Executive Operations & Logistics Risk Management Dashboard
> Project: COMP8035041 Big Data Analytics – Binus Graduate Program
> Student: Rafael Satriaprima Yudianto (2702752495)

---

## 1. Character & Core Purpose

This dashboard is an industrial decision-support tool designed for supply chain directors and dispatch supervisors. Its purpose is to transform PySpark machine learning risk scores and bipartite network graph topology into immediate operational decisions (dispatch prioritization, fast-track picking, and warehouse slotting).

The aesthetic is **Industrial Precision / Executive Operations**: crisp, high-density, legible, and devoid of decorative gimmicks, soft floating cards, or rainbow gradients.

---

## 2. Color Palette & Hierarchy

- **Base Canvas:** `#f8fafc` (Slate 50) – clean, neutral background.
- **Card Surfaces:** `#ffffff` (White) with crisp `#e2e8f0` (Slate 200) borders.
- **Typography Primary:** `#0f172a` (Slate 900) – high contrast (16:1 against white).
- **Typography Secondary:** `#475569` (Slate 600) – metadata and descriptions (min. 5.5:1 against white, exceeds WCAG AA).
- **Primary Operational Accent:** `#1e40af` (Blue 800) – active filters, primary headers.
- **Critical Risk Accent (Sole Alert Color):** `#b91c1c` (Red 700) – reserved strictly for orders exceeding the risk threshold, late delivery warnings, and urgent intervention queues.
- **Network / Analytics Accent:** `#334155` (Slate 700) / `#475569` – technical graph connection degrees.

*No arbitrary neon, purple, or pastel gradients. Red is strictly functional, signalling urgency.*

---

## 3. Typography & Numerical Data

- **Primary Typeface:** `Plus Jakarta Sans`, sans-serif. Clean, geometric, legible at small sizes.
- **Data & Numeric Values:** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` with `font-variant-numeric: tabular-nums` to guarantee aligned columns in tables and KPI metrics.

---

## 4. Component Standards & Layout

- **Border Radius:** `rounded-lg` (8px) for cards, `rounded-md` (6px) for inputs and buttons. No pill-shaped buttons or generic floating blobs.
- **Elevation:** Flat border-driven layout (`border border-slate-200`). Subtle shadow (`shadow-xs`) used only on active floating controls.
- **Interactive Controls:** Explicit high-contrast focus rings (`focus:ring-2 focus:ring-slate-900 focus:ring-offset-2`).
- **States:** Complete handling of Loading, Error, Empty, and Populated states.

---

## 5. Antislop Dials

- **Energy:** 2 (Professional, high-utility, purposeful)
- **Rhythm:** 2 (Structured grid with clear visual anchors)
- **Motion:** 1 (Instant transitions, zero decorative delay)
