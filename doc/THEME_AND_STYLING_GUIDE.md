# 🎨 UI Theme & Styling Guide: Transport GPS Tracking System

This document specifies the color palettes, contrast standards, and theme scoping rules for the **Transport GPS Tracking System**, ensuring accessible, high-contrast readability across both **Dark Theme** and **Light Theme**.

---

## 1. Theme Architecture Overview

The application implements a dual-mode CSS variable token system toggled dynamically via [`ThemeManager`](file:///c:/Users/Rohan/Downloads/Transport_GPS_Tracking/frontend/assets/js/utils.js#L164) and persisted in browser `localStorage` (`tgt_theme`).

Theme attributes are set at the root element:
```html
<html lang="en" data-bs-theme="dark" data-theme="dark">
<!-- OR -->
<html lang="en" data-bs-theme="light" data-theme="light">
```

---

## 2. Color Tokens Specification

| Token | Dark Theme (Default) | Light Theme | Usage |
| :--- | :--- | :--- | :--- |
| `--bg-main` | `#090D16` | `#F1F5F9` | Main page background |
| `--bg-surface` | `#0F172A` | `#FFFFFF` | Cards, tables, sidebars, modals |
| `--bg-surface-elevated`| `#1E293B` | `#F8FAFC` | Dropdowns, hover states |
| `--text-main` | `#FFFFFF` | `#000000` | Primary titles, vehicle & driver names, bold text |
| `--text-secondary` | `#E2E8F0` | `#1E293B` | Subtitles, body data |
| `--text-label` | `#E2E8F0` | `#000000` | Form labels, card captions |
| `--text-muted` | `#94A3B8` | `#64748B` | Subtle hints, timestamps |
| `--border-color` | `rgba(255, 255, 255, 0.14)` | `#CBD5E1` | Card boundaries, dividers |
| `--primary` | `#3B82F6` | `#2563EB` | Action buttons, active badges |

---

## 2.1 Light Theme Bold Color Standard (Strict Black `#000000`)

To guarantee maximum accessibility, contrast, and visual punch across light mode:
- **All Bold Typography**: Elements marked with `b`, `strong`, `.fw-bold`, `.fw-bolder`, `.fw-semibold`, `font-weight: 700`, `font-weight: 800`, or `font-weight: 600` are strictly set to **solid black (`#000000 !important`)**.
- **Headings & Titles**: `h1` through `h6`, `.topbar-title h4`, `.brand-text h5`, `.card-header`, `.modal-title`, and `.auth-card h4` are strictly **solid black (`#000000 !important`)**.
- **Data Values & Metrics**: KPI values (`.kpi-value`), table headers (`.custom-table th`), vehicle registration numbers, and driver detail values default to **solid black (`#000000 !important`)**.
- **Form Labels**: `.form-label`, `label.form-label`, and `label` are enforced in bold solid black (`#000000 !important`, font-weight 700).
- **Exceptions**: Status-indicating utility classes (`.text-success`, `.text-danger`, `.text-warning`, `.text-info`, `.text-primary`), `.badge`, and action buttons (`.btn`) retain their respective functional branding colors.

---

## 3. Driver Details & Roster Card Styling

To prevent contrast clashes when switching between dark and light themes, driver cards enforce strict theme scoping:

### 3.1 Dark Theme Rules
- **Card Background**: `#0F172A` (deep cyber navy).
- **Driver Name (`.driver-card-name`)**: `#FFFFFF` (crisp bold white, font-weight 800).
- **Captions (`.driver-card-label`)**: `#CBD5E1` (bright readable slate, **never black on dark background**).
- **Detail Values (`.driver-card-val`)**: `#FFFFFF` (crisp white, font-weight 700).
- **License Badge (`.driver-card-lic code`)**: `#F8FAFC` on translucent dark background with border.

### 3.2 Light Theme Rules
- **Card Background**: `#FFFFFF` (pure white with subtle shadow).
- **Driver Name (`.driver-card-name`)**: `#000000` (bold solid black, font-weight 800).
- **Captions (`.driver-card-label`)**: `#000000` (bold solid black, font-weight 700).
- **Detail Values (`.driver-card-val`)**: `#000000` (bold solid black, font-weight 700).
- **License Badge (`.driver-card-lic code`)**: `#000000` on `#E2E8F0` background.

---

## 4. Modal Dialogs & Form Inputs

### Register & Edit Driver Modals
1. **Modal Header Title**: Solid black (`#000000`, font-weight 800).
2. **Field Labels** (`FIRST NAME *`, `PHONE NUMBER *`, `LICENSE NUMBER *`, etc.):
   - Enforced in solid black (`#000000`, font-weight 700).
   - Removed faded grey classes to maintain maximum legibility.
3. **Form Inputs (`.form-control`, `.form-select`)**:
   - Light Theme: `#000000` input text on `#FFFFFF` background with crisp `#94A3B8` borders.
   - Dark Theme: `#FFFFFF` input text on `#131E36` background with `#3B82F6` focus rings.
   - Placeholders: Styled in clear, legible `#64748B`.

---

## 5. Cache Invalidation & Versioning

To ensure clients immediately receive stylesheet and JavaScript updates without stale browser caching:
- Stylesheet links: `<link rel="stylesheet" href="assets/css/components.css?v=1.3.0">`
- Script links: `<script src="assets/js/drivers.js?v=1.3.0"></script>`
