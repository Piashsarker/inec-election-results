# BOXI Tracker — Full Requirements Analysis

## 1. Design Brief

- **Product**: BOXI Tracker (www.boxitracker.com) — Nigeria's premier election monitoring platform
- **Primary Users**: Nigerian voters, journalists, election observers, researchers, civil society organizations
- **Primary Goal**: Access real-time, verified election results with geographic drill-down and analytics
- **Business Goal**: Become the go-to independent source for Nigerian election data; drive daily active usage through live updates and social sharing
- **Success Metrics**: Daily active users during elections, result verification accuracy, social shares, time-on-site
- **Brand Signals**: Trust, transparency, Nigerian identity, data authority, civic empowerment
- **Constraints**: Next.js 14, Tailwind CSS, mobile-first (60%+ mobile traffic expected), offline-capable, multilingual

---

## 2. What We Have vs What's Needed

### Currently Built (Existing Codebase)

| Feature | Status | Notes |
|---------|--------|-------|
| Dashboard with stats cards | ✅ Built | Basic stats, quick actions |
| Interactive Nigeria map | ✅ Built | State-level SVG map with election type selector |
| Election type browsing | ✅ Built | Type → State → LGA → Ward → PU drill-down |
| Results listing with filters | ✅ Built | Table with sort, search, pagination |
| Result detail page | ✅ Built | Party bar charts, confidence score, flag action |
| Aggregation page | ✅ Built | Ward/LGA/State level aggregation |
| Dark/light mode | ✅ Built | Theme toggle in nav |
| Export (CSV/JSON) | ✅ Built | ExportCenter component |
| Job monitoring | ✅ Built | JobMonitor component |
| Backend scraper + OCR | ✅ Built | Full pipeline: scrape → OCR → extract → validate |
| API (FastAPI) | ✅ Built | Results, elections, aggregation, jobs, export endpoints |

### Gap: New Features Required by BOXI Tracker

| # | Feature | Priority | Category |
|---|---------|----------|----------|
| 1 | **Complete UI/UX Redesign** | Critical | Design |
| 2 | **Live Results Dashboard** (real-time updates) | Critical | Frontend |
| 3 | **Polling Unit Location with Google Maps** | Critical | Frontend + Backend |
| 4 | **Uploaded Result Verification** (image vs extracted comparison) | Critical | Frontend |
| 5 | **Push Notifications** | High | Frontend + Backend |
| 6 | **Follow State/Candidate** | High | Frontend + Backend |
| 7 | **Shareable Result Cards** (social OG images) | High | Frontend |
| 8 | **Turnout Analytics** (demographics: youth, female, senior) | High | Frontend + Backend |
| 9 | **Incident Monitoring / Live Incident Map** | High | Full-stack |
| 10 | **Election Pulse Index** (health score 0–100) | High | Backend + Frontend |
| 11 | **Historical Election Comparison** | Medium | Backend + Frontend |
| 12 | **AI Election Insights Feed** (NL summaries) | Medium | Backend (LLM) + Frontend |
| 13 | **PVC Collection Tracking** | Medium | Full-stack |
| 14 | **Pending Upload Tracking** (predicted completion) | Medium | Backend + Frontend |
| 15 | **Multilingual Support** (EN, Hausa, Yoruba, Igbo, Pidgin) | Medium | Frontend (i18n) |
| 16 | **Voice Search** | Low | Frontend |
| 17 | **Voice Reading (TTS)** | Low | Frontend |
| 18 | **Offline Mode (PWA)** | Medium | Frontend |
| 19 | **Large Text / High Contrast Modes** | Low | Frontend (accessibility) |
| 20 | **Competitive State Ranking** | Low | Backend + Frontend |
| 21 | **Voter Participation Score** | Low | Backend + Frontend |

---

## 3. Information Architecture (BOXI Tracker)

### Navigation Model (Global)

```
┌─────────────────────────────────────────────────────┐
│  🇳🇬 BOXI Tracker    [Search / Voice]    [🔔] [👤]  │
├─────────────────────────────────────────────────────┤
│  Dashboard | Map | Results | Insights | More ▼      │
│                                    ├── Verification │
│                                    ├── Incidents    │
│                                    ├── Turnout      │
│                                    ├── PVC Track    │
│                                    └── Settings     │
└─────────────────────────────────────────────────────┘
```

### Page Purpose Statements

| Page | Purpose |
|------|---------|
| Dashboard | At-a-glance election health: pulse score, top contests, upload progress, live feed |
| Interactive Map | Geographic exploration: state → LGA → ward → PU with winner overlay |
| Results | Search, filter, sort all extracted polling unit results |
| Result Detail | Single PU: party bars, source image, verification score, flag action |
| Verification | Side-by-side: uploaded sheet image vs extracted data, trust rating |
| Insights | AI-generated summaries, trends, comparisons, competitive rankings |
| Turnout Analytics | Demographic participation: youth/female/senior by geography |
| Incident Map | Live map of reported election irregularities/violence |
| PVC Collection | Track PVC distribution by state/LGA |
| Pending Uploads | Which PUs haven't reported; predicted completion time |
| Notifications | User's followed states/candidates, alert preferences |
| Settings | Language, accessibility, offline preferences, dark mode |

### Key User Paths

**Path 1: "What's the latest result in my state?"**
1. Land on Dashboard → see pulse score + top contests
2. Tap state on map OR search "Kano"
3. See state aggregation with party breakdown
4. Drill into LGA → Ward → specific Polling Unit
5. View result detail + verification score
6. Share via social card

**Path 2: "Is this election fair?"**
1. Land on Dashboard → see Election Pulse Index
2. Navigate to Insights → AI summary feed
3. Check Incident Map for irregularities
4. View Verification page for flagged results
5. Compare with historical election data

**Path 3: "Follow my candidate's progress"**
1. Register/follow a party or candidate
2. Receive push notification when new results come in
3. View live updating dashboard filtered to followed entity
4. Share progress card on social media

---

## 4. UI/UX Design System (BOXI Tracker)

### Aesthetic Direction

**Tone**: Editorial/data-journalism meets civic tech — authoritative, clean, Nigerian identity
**Not**: Generic dashboard. Not a portfolio. Not flashy for its own sake.
**Memorable element**: The interactive Nigeria map as the visual centrepiece, with the Election Pulse Index as the hook metric.

### Design Tokens

```css
:root {
  /* Spacing scale (px) */
  --space-0: 0;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;
  --space-24: 96px;

  /* Typography — distinctive pairing */
  --font-display: 'Playfair Display', serif;  /* Headlines — editorial authority */
  --font-body: 'DM Sans', sans-serif;         /* Body — clean, modern readability */
  --font-mono: 'JetBrains Mono', monospace;   /* Data/codes */

  /* Type scale */
  --text-xs: 0.75rem;    /* 12px — captions, meta */
  --text-sm: 0.875rem;   /* 14px — secondary body */
  --text-base: 1rem;     /* 16px — body */
  --text-lg: 1.25rem;    /* 20px — subheading */
  --text-xl: 1.5rem;     /* 24px — section head */
  --text-2xl: 1.875rem;  /* 30px — page title */
  --text-3xl: 2.5rem;    /* 40px — hero */
  --text-4xl: 3.5rem;    /* 56px — hero number/score */

  /* Colours — Nigerian identity + data authority */
  --green-50: #f0fdf4;
  --green-100: #dcfce7;
  --green-500: #008751;   /* Nigerian green — primary */
  --green-600: #006b40;
  --green-700: #005432;
  --green-900: #052e16;

  --white: #ffffff;        /* Nigerian white — clean backgrounds */

  --neutral-50: #fafafa;
  --neutral-100: #f5f5f5;
  --neutral-200: #e5e5e5;
  --neutral-300: #d4d4d4;
  --neutral-500: #737373;
  --neutral-700: #404040;
  --neutral-800: #262626;
  --neutral-900: #171717;

  --accent-gold: #d4a843;     /* Warm accent — highlights, pulse score */
  --accent-red: #dc2626;      /* Alerts, incidents, flagged */
  --accent-blue: #2563eb;     /* Links, info */
  --accent-amber: #f59e0b;    /* Warnings, in-progress */

  /* Party colours */
  --party-apc: #1e40af;
  --party-pdp: #dc2626;
  --party-lp: #16a34a;
  --party-nnpp: #7c3aed;
  --party-apga: #ea580c;

  /* Elevation / shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
  --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.06);

  /* Radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Borders */
  --border-default: 1px solid var(--neutral-200);
  --border-subtle: 1px solid var(--neutral-100);
}

/* Dark mode overrides */
[data-theme="dark"] {
  --neutral-50: #171717;
  --neutral-100: #262626;
  --neutral-200: #404040;
  --neutral-300: #525252;
  --neutral-500: #a3a3a3;
  --neutral-700: #d4d4d4;
  --neutral-800: #e5e5e5;
  --neutral-900: #fafafa;
}
```

### Motion Rules

- Page transitions: fade + slide-up (200ms ease-out)
- Cards: scale(1.02) on hover with shadow-lg transition
- Map states: fill transition 150ms on hover
- Numbers/stats: count-up animation on load (500ms)
- Stagger: dashboard cards reveal with 50ms delay between each
- Reduced motion: respect `prefers-reduced-motion`, disable all transforms

---

## 5. Component Inventory

### Core Components (Shared)

| Component | States | Notes |
|-----------|--------|-------|
| `NavBar` | default, mobile-open, scrolled (sticky) | Logo + links + search + notifications + profile |
| `SearchBar` | idle, focused, loading, results, empty | Supports voice input |
| `StatCard` | default, loading (skeleton), empty | Number + label + trend indicator |
| `MapSvg` | idle, hover-state, selected-state, loading | Interactive SVG with colour scale |
| `PartyBar` | default, animated (count-up) | Horizontal bar with party colour + percentage |
| `ResultCard` | default, hover, expanded | Polling unit result summary |
| `ShareCard` | generating, ready, copied | Social media OG image preview |
| `PulseScore` | default, loading | Circular gauge 0–100 |
| `NotificationBell` | idle, has-new, dropdown-open | Badge count + dropdown list |
| `LanguageSwitcher` | closed, open | 5 language options |
| `InsightCard` | default, loading | AI-generated text summary with source citation |
| `IncidentMarker` | default, selected, resolved | Map pin with severity colour |
| `VerificationWidget` | side-by-side image + extracted data | Match/mismatch highlighting |
| `OfflineBanner` | visible (offline), hidden (online) | Persistent top banner |
| `SkeletonLoader` | pulse animation | For all async data |

### Page-Specific Components

| Page | Components |
|------|------------|
| Dashboard | `PulseScore`, `TopContestants`, `MapSvg` (mini), `LiveFeed`, `UploadProgress` |
| Map | `MapSvg` (full), `StateDetailPanel`, `ElectionTypeSelector`, `MapLegend` |
| Results | `ResultsTable`, `FilterBar`, `Pagination`, `ResultCard` |
| Result Detail | `PartyBar` (×N), `StatCard` (×4), `VerificationWidget`, `FlagButton` |
| Insights | `InsightCard` (feed), `CompetitiveRanking`, `HistoricalChart` |
| Incidents | `IncidentMap`, `IncidentList`, `IncidentDetail`, `SeverityFilter` |
| Turnout | `DemographicChart`, `StateComparisonTable`, `ParticipationScore` |

---

## 6. Full Requirement List (Prioritized)

### Phase 1 — Core Redesign (Weeks 1–4)

| # | Requirement | Type |
|---|-------------|------|
| 1.1 | Rebrand to BOXI Tracker (logo, name, meta) | UI |
| 1.2 | Implement new design token system (fonts, colours, spacing) | UI |
| 1.3 | Redesign navigation (search bar, notification bell, language switcher) | UI |
| 1.4 | Redesign Dashboard with Election Pulse Index + top contestants | UI |
| 1.5 | Enhance interactive map with better colour scale + state tooltips | UI |
| 1.6 | Add skeleton loading states to all data-fetching components | UI |
| 1.7 | Implement dark mode with proper token switching | UI |
| 1.8 | Mobile-first responsive pass on all existing pages | UI |
| 1.9 | Add page transition animations (stagger reveals) | UI |
| 1.10 | Implement shareable result cards (OG image generation) | Frontend |

### Phase 2 — New Features (Weeks 5–8)

| # | Requirement | Type |
|---|-------------|------|
| 2.1 | Polling unit location with Google Maps integration | Full-stack |
| 2.2 | Uploaded result verification page (image vs data side-by-side) | Frontend |
| 2.3 | Follow state/candidate system (user preferences) | Full-stack |
| 2.4 | Push notifications (web push API) | Full-stack |
| 2.5 | Incident monitoring system (report + map) | Full-stack |
| 2.6 | Turnout analytics with demographic breakdowns | Backend + Frontend |
| 2.7 | Pending upload tracking with predicted completion ETA | Backend + Frontend |
| 2.8 | Election Pulse Index scoring algorithm | Backend |
| 2.9 | Historical election data import + comparison UI | Full-stack |
| 2.10 | Live real-time updates via WebSocket/SSE | Full-stack |

### Phase 3 — Premium/Advanced (Weeks 9–12)

| # | Requirement | Type |
|---|-------------|------|
| 3.1 | AI Election Insights Feed (LLM-generated summaries) | Backend (LLM) + Frontend |
| 3.2 | Competitive state ranking | Backend + Frontend |
| 3.3 | Voter participation score by demographics | Backend + Frontend |
| 3.4 | PVC collection tracking module | Full-stack |
| 3.5 | Multilingual support (i18n: EN, Hausa, Yoruba, Igbo, Pidgin) | Frontend |
| 3.6 | Offline mode (PWA with service worker + cached data) | Frontend |
| 3.7 | Voice search integration (Web Speech API) | Frontend |
| 3.8 | Voice reading / text-to-speech | Frontend |
| 3.9 | Large text + high contrast accessibility modes | Frontend |
| 3.10 | Predictive upload completion algorithm | Backend |

---

## 7. States & Edge Cases

| Component/Page | Edge Case | Handling |
|----------------|-----------|----------|
| Dashboard | No results yet (pre-election) | Show "Election Day: [date]. Results will appear here." with countdown |
| Map | State with 0 processed PUs | Grey fill + "No data yet" tooltip |
| Results table | Empty search results | "No results match your filters. Try broadening your search." |
| Verification | Image fails to load | Placeholder + "Source image unavailable" message |
| Pulse Index | Insufficient data for scoring | Show "--/100" with explanation |
| Notifications | User not registered | Prompt to enable notifications with benefit copy |
| Offline mode | Stale cached data | Banner: "You're viewing cached data from [timestamp]. Connect to refresh." |
| Incident map | No incidents reported | "No incidents reported. This is good news! 🎉" |
| Share card | Long party names | Truncate with ellipsis; tooltip on hover |
| Multilingual | Missing translation key | Fall back to English; log warning |

---

## 8. Accessibility Requirements

- Colour contrast: ≥ 4.5:1 for body text, ≥ 3:1 for large text
- All interactive elements keyboard accessible with visible focus ring
- Map: keyboard-navigable states (arrow keys); screen reader announces state name + leading party
- Charts: provide data table alternative for screen readers
- Animations: respect `prefers-reduced-motion`
- Forms: proper `<label>` associations, live error announcements via `aria-live`
- Language: `lang` attribute updates on language switch
- Touch targets: minimum 44×44px on mobile

---

## 9. Technical Implementation Notes

### Frontend Changes Needed

- **Font loading**: Add `Playfair Display` + `DM Sans` via `next/font/google`
- **i18n**: Use `next-intl` or `react-i18next` for multilingual
- **PWA**: Add `next-pwa` plugin + service worker + manifest.json
- **Real-time**: WebSocket or SSE connection for live result updates
- **Maps**: `@react-google-maps/api` for polling unit locations
- **Social sharing**: `next/og` (or `@vercel/og`) for dynamic OG images
- **Push notifications**: Web Push API + backend subscription management
- **Charts**: Enhance Recharts usage for turnout/demographic visualizations

### Backend Changes Needed

- **WebSocket endpoint** for live result streaming
- **Notification service** (web-push library + subscription storage)
- **Incident model + API** (CRUD + geographic queries)
- **Pulse Index algorithm** (composite score from multiple signals)
- **User preferences model** (followed states/candidates/parties)
- **Historical data import** (previous election CSVs)
- **AI insights endpoint** (LLM summarization of trends)
- **PVC collection model + API**
- **Predictive completion** (time-series extrapolation)

---

## 10. Summary: Current vs BOXI Tracker

```
CURRENT STATE (boxitracker.com)
├── ✅ Scraping pipeline (Playwright + OCR)
├── ✅ Basic dashboard + stats
├── ✅ Nigeria map (SVG, state-level)
├── ✅ Results browsing + detail
├── ✅ Aggregation (ward/LGA/state)
├── ✅ Export (CSV/JSON)
├── ✅ Job monitoring
├── ✅ Dark mode
└── ✅ FastAPI backend + PostgreSQL

BOXI TRACKER (target)
├── 🔄 Complete UI redesign (new brand, tokens, typography)
├── 🆕 Election Pulse Index
├── 🆕 Live real-time updates (WebSocket)
├── 🆕 Google Maps polling unit locations
├── 🆕 Result verification (image comparison)
├── 🆕 Follow state/candidate + notifications
├── 🆕 Shareable social cards
├── 🆕 Incident monitoring + map
├── 🆕 Turnout demographics
├── 🆕 AI insights feed
├── 🆕 Historical comparison
├── 🆕 Multilingual (5 languages)
├── 🆕 Offline mode (PWA)
├── 🆕 Voice search + TTS
├── 🆕 PVC tracking
├── 🆕 Pending upload predictions
├── 🆕 Competitive state rankings
└── 🆕 Accessibility modes (large text, high contrast)
```

**Effort estimate**: The current codebase covers ~25% of BOXI Tracker's scope. Phase 1 (redesign) is primarily frontend. Phases 2–3 require substantial backend additions.
