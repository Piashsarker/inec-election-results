# BOXI Tracker — Development Plan

## Overview

Transform the existing INEC Election Results Agent into **BOXI Tracker** (www.boxitracker.com) — a public-facing Nigerian election monitoring platform with real-time results, interactive maps, analytics, and social features.

**Current state**: Backend data pipeline (scraping, OCR, extraction, aggregation) + basic dashboard frontend.
**Target state**: Full-featured election monitoring platform with 11 screens, real-time updates, multilingual support, and premium analytics.

---

## Phase 1: Core Redesign & Brand Identity (Weeks 1–3)

### Sprint 1.1 — Design System & Brand (Week 1)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1.1.1 | Set up BOXI Tracker brand assets (logo, favicon, meta tags) | None |
| 1.1.2 | Implement design token system (CSS variables: colours, spacing, radii, shadows) | None |
| 1.1.3 | Replace Inter font with Playfair Display (display) + DM Sans (body) | None |
| 1.1.4 | Create base component library (Button, Card, Badge, Input, Select) | 1.1.2 |
| 1.1.5 | Implement skeleton loading component | 1.1.2 |
| 1.1.6 | Set up dark mode token switching with new palette | 1.1.2 |
| 1.1.7 | Create responsive layout primitives (Container, Grid, Stack) | 1.1.2 |

### Sprint 1.2 — Navigation & Layout (Week 2)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1.2.1 | Redesign global navigation bar (logo, links, search, notifications, profile) | 1.1.4 |
| 1.2.2 | Build mobile navigation (hamburger menu + slide-out drawer) | 1.2.1 |
| 1.2.3 | Implement search bar with autocomplete (states, LGAs, PU codes) | 1.2.1 |
| 1.2.4 | Add page transition animations (fade + slide-up stagger) | 1.1.2 |
| 1.2.5 | Redesign footer with language switcher + accessibility options | 1.1.4 |
| 1.2.6 | Implement breadcrumb navigation for drill-down pages | 1.1.4 |

### Sprint 1.3 — Dashboard Redesign (Week 3)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1.3.1 | Build Election Pulse Index gauge component (circular score 0–100) | 1.1.4 |
| 1.3.2 | Redesign top contestants section with party colours + count-up animation | 1.1.4 |
| 1.3.3 | Create upload progress widget (% of PUs reporting) | 1.1.5 |
| 1.3.4 | Build live activity feed component (latest results streaming in) | 1.1.4 |
| 1.3.5 | Redesign map preview card on dashboard | 1.1.4 |
| 1.3.6 | Add stat cards with trend indicators and animations | 1.1.5 |
| 1.3.7 | Mobile-first responsive pass on full dashboard | 1.3.1–1.3.6 |

---

## Phase 2: Enhanced Map & Results (Weeks 4–6)

### Sprint 2.1 — Interactive Map Enhancement (Week 4)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 2.1.1 | Improve map colour scale with party-winner gradient | Phase 1 |
| 2.1.2 | Add state tooltip with quick stats (leading party, turnout %, PUs reporting) | Phase 1 |
| 2.1.3 | Implement LGA drill-down (click state → show LGA boundaries) | Phase 1 |
| 2.1.4 | Add map legend with dynamic party colours + turnout scale | Phase 1 |
| 2.1.5 | Build state detail panel (slide-in from right on state select) | Phase 1 |
| 2.1.6 | Add Google Maps integration for polling unit locations | API key setup |
| 2.1.7 | Implement polling unit location page with GPS coordinates | 2.1.6 |

### Sprint 2.2 — Results & Verification (Week 5)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 2.2.1 | Redesign results table with new design system | Phase 1 |
| 2.2.2 | Build result detail page redesign (party bars, confidence, metadata) | Phase 1 |
| 2.2.3 | Create verification page (side-by-side: uploaded image vs extracted data) | Phase 1 |
| 2.2.4 | Add verification confidence score with visual indicator | 2.2.3 |
| 2.2.5 | Implement result flagging workflow (flag → review → resolve) | 2.2.2 |
| 2.2.6 | Add shareable result cards (generate OG image per result) | Phase 1 |
| 2.2.7 | Social share buttons (Twitter, WhatsApp, Facebook, copy link) | 2.2.6 |

### Sprint 2.3 — Real-time & Notifications (Week 6)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 2.3.1 | Backend: WebSocket/SSE endpoint for live result streaming | None (backend) |
| 2.3.2 | Frontend: WebSocket client hook + live-updating components | 2.3.1 |
| 2.3.3 | Backend: User preferences model (followed states/candidates/parties) | None (backend) |
| 2.3.4 | Frontend: Follow state/candidate UI (follow button + preferences page) | 2.3.3 |
| 2.3.5 | Backend: Web Push notification service (subscription + send) | 2.3.3 |
| 2.3.6 | Frontend: Push notification opt-in + notification bell dropdown | 2.3.5 |
| 2.3.7 | Backend: Notification triggers (new result in followed area) | 2.3.5 |

---

## Phase 3: Analytics & Insights (Weeks 7–9)

### Sprint 3.1 — Turnout & Demographics (Week 7)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 3.1.1 | Backend: Turnout analytics calculation endpoint | None (backend) |
| 3.1.2 | Frontend: Turnout analytics page with demographic charts | 3.1.1 |
| 3.1.3 | Build voter participation score component (youth/female/senior) | 3.1.1 |
| 3.1.4 | State comparison table (sortable by turnout metrics) | 3.1.1 |
| 3.1.5 | Backend: Election Pulse Index scoring algorithm | None (backend) |
| 3.1.6 | Frontend: Pulse Index detail breakdown (what contributes to score) | 3.1.5 |

### Sprint 3.2 — Incidents & Monitoring (Week 8)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 3.2.1 | Backend: Incident model + CRUD API | None (backend) |
| 3.2.2 | Backend: Incident geographic query (by state/LGA) | 3.2.1 |
| 3.2.3 | Frontend: Incident monitoring map (pins with severity colours) | 3.2.1 |
| 3.2.4 | Frontend: Incident list with filters (type, severity, state) | 3.2.1 |
| 3.2.5 | Frontend: Incident detail panel (description, source, status) | 3.2.1 |
| 3.2.6 | Frontend: Incident report form (for observers to submit) | 3.2.1 |

### Sprint 3.3 — Historical & Comparison (Week 9)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 3.3.1 | Backend: Historical election data import (previous elections CSV) | None (backend) |
| 3.3.2 | Backend: Comparison API (current vs previous by geography) | 3.3.1 |
| 3.3.3 | Frontend: Historical comparison page (side-by-side results) | 3.3.2 |
| 3.3.4 | Frontend: Trend charts (turnout/margins over elections) | 3.3.2 |
| 3.3.5 | Backend: Competitive state ranking algorithm | None (backend) |
| 3.3.6 | Frontend: Competitive state ranking table + visualization | 3.3.5 |

---

## Phase 4: Premium Features (Weeks 10–12)

### Sprint 4.1 — AI Insights & Intelligence (Week 10)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 4.1.1 | Backend: AI insights generation (LLM summarization of trends) | OpenAI API |
| 4.1.2 | Backend: Insights scheduling (generate every N minutes during election) | 4.1.1 |
| 4.1.3 | Frontend: AI Insights feed page (card-based, timestamped) | 4.1.1 |
| 4.1.4 | Frontend: Inline insights on dashboard (rotating summary) | 4.1.1 |
| 4.1.5 | Backend: Predictive upload completion algorithm | None (backend) |
| 4.1.6 | Frontend: Pending uploads page with ETA prediction | 4.1.5 |

### Sprint 4.2 — Multilingual & Accessibility (Week 11)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 4.2.1 | Set up i18n framework (next-intl) with locale routing | None |
| 4.2.2 | Create translation files: English (base) | 4.2.1 |
| 4.2.3 | Create translation files: Hausa | 4.2.1 |
| 4.2.4 | Create translation files: Yoruba | 4.2.1 |
| 4.2.5 | Create translation files: Igbo | 4.2.1 |
| 4.2.6 | Create translation files: Pidgin | 4.2.1 |
| 4.2.7 | Language switcher UI integration | 4.2.1 |
| 4.2.8 | Implement large text mode (accessibility setting) | None |
| 4.2.9 | Implement high contrast mode | None |
| 4.2.10 | Full accessibility audit and fixes (WCAG 2.1 AA) | All above |

### Sprint 4.3 — Offline & Voice (Week 12)

| Task | Description | Dependencies |
|------|-------------|--------------|
| 4.3.1 | Configure PWA (next-pwa, manifest.json, service worker) | None |
| 4.3.2 | Implement offline data caching strategy (recent states + saved reports) | 4.3.1 |
| 4.3.3 | Build offline banner component (shows cached data timestamp) | 4.3.1 |
| 4.3.4 | Implement voice search (Web Speech API recognition) | None |
| 4.3.5 | Implement text-to-speech for results reading | None |
| 4.3.6 | Backend: PVC collection tracking model + API | None (backend) |
| 4.3.7 | Frontend: PVC collection tracking page | 4.3.6 |
| 4.3.8 | Final QA pass: cross-browser, mobile devices, performance audit | All |
| 4.3.9 | Production deployment + DNS switch to boxitracker.com | All |

---

## Testing & QA (Ongoing)

| Activity | Frequency |
|----------|-----------|
| Unit tests for new backend endpoints | Per sprint |
| Component visual testing (Storybook or manual) | Per sprint |
| Mobile device testing (iOS Safari, Android Chrome) | Per sprint |
| Accessibility testing (axe, keyboard navigation) | Per phase |
| Performance audit (Lighthouse, Core Web Vitals) | Per phase |
| Cross-browser testing (Chrome, Firefox, Safari, Edge) | Before release |
| Load testing (concurrent users during election simulation) | Before launch |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Google Maps API costs at scale | Medium | Cache results; use free tier initially; fallback to static maps |
| LLM costs for AI insights | Medium | Rate limit generation; cache summaries; use cheaper models for bulk |
| Real-time load during election day | High | Horizontal scaling; Redis pub/sub; CDN for static assets |
| Translation accuracy (5 languages) | Medium | Use professional translators for key UI; community review |
| INEC portal changes breaking scraper | High | Scraper monitoring; alert system; manual fallback |
| Offline sync conflicts | Low | Last-write-wins for read-only data; no user-generated content offline |

---

## Definition of Done

A feature is complete when:
- [ ] Functional on desktop (Chrome, Firefox, Safari)
- [ ] Functional on mobile (iOS Safari, Android Chrome)
- [ ] Dark mode works correctly
- [ ] Loading/empty/error states implemented
- [ ] Keyboard accessible
- [ ] Screen reader tested (VoiceOver / NVDA basics)
- [ ] No lint/type errors
- [ ] Backend endpoint has basic tests
- [ ] Deployed to staging and verified
