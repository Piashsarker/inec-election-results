# Work Order: BOXI Tracker Platform Development

**Project**: BOXI Tracker — Nigerian Election Monitoring Platform
**Domain**: www.boxitracker.com
**Prepared by**: [Your Company Name]
**Date**: June 2026
**Rate**: £10/hour (Senior Full-Stack Developer)

---

## 1. Project Summary

Development of BOXI Tracker, a comprehensive Nigerian election monitoring and insights platform. The project transforms an existing backend data pipeline (scraping, OCR, result extraction) into a full public-facing product with real-time results, interactive maps, analytics, social features, and accessibility compliance.

**Tech Stack**: Next.js 14 (TypeScript), FastAPI (Python), PostgreSQL, Redis, Tailwind CSS

---

## 2. Work Already Completed (Pre-existing — Not Billed)

The following has already been delivered and is excluded from this estimate:

| Item | Description |
|------|-------------|
| Backend scraping pipeline | Playwright-based INEC portal scraper with retry logic |
| OCR engine | Dual-engine (Tesseract + GPT-4 Vision) extraction system |
| Data extraction & validation | Structured parser with confidence scoring |
| Result aggregation service | Ward/LGA/State level vote aggregation |
| FastAPI REST API | Elections, results, aggregation, jobs, export endpoints |
| PostgreSQL database | Full schema: elections, geography, results, jobs |
| Basic frontend dashboard | Stats, quick actions, map preview |
| Interactive Nigeria SVG map | State-level map with election type selector |
| Results browsing & detail | Table with filters, sort, pagination; detail view |
| Aggregation page | Ward/LGA/State level aggregation |
| Export (CSV/JSON) | Export with filters |
| Job monitoring | Scraping job tracking |
| Dark/light mode | Theme toggle |
| Docker deployment | Production Docker Compose with Nginx + Certbot SSL |
| VPS deployment | Automated deployment scripts |

---

## 3. Scope of Work & Estimates

### Phase 1: Core Redesign & Brand Identity

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 1.1 | Design system setup (tokens: colours, spacing, typography, shadows) | 5 | 50 |
| 1.2 | Font integration (Playfair Display + DM Sans) + global type update | 2 | 20 |
| 1.3 | Brand assets: BOXI Tracker logo, favicon, meta tags | 2 | 20 |
| 1.4 | Core component library (Button, Card, Badge, Input, Select) | 8 | 80 |
| 1.5 | Skeleton loading states | 3 | 30 |
| 1.6 | Dark mode with new palette | 3 | 30 |
| 1.7 | Global navigation redesign (desktop + mobile drawer) | 6 | 60 |
| 1.8 | Search bar with autocomplete | 5 | 50 |
| 1.9 | Dashboard redesign: Pulse Index + top contestants + stats | 10 | 100 |
| 1.10 | Dashboard: map preview + live feed widget | 5 | 50 |
| 1.11 | Page animations (transitions + stagger reveals) | 3 | 30 |
| 1.12 | Mobile-first responsive pass (all pages) | 6 | 60 |
| | **Phase 1 Subtotal** | **58** | **£580** |

### Phase 2: Enhanced Map, Results & Verification

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 2.1 | Map: improved colour scale + party-winner overlay | 3 | 30 |
| 2.2 | Map: state tooltip with quick stats | 3 | 30 |
| 2.3 | Map: LGA drill-down on state click | 8 | 80 |
| 2.4 | Map: state detail slide-in panel | 4 | 40 |
| 2.5 | Google Maps for polling unit locations | 6 | 60 |
| 2.6 | Polling unit location page (address, GPS, PU code) | 4 | 40 |
| 2.7 | Results table + detail page redesign | 5 | 50 |
| 2.8 | Verification page (image vs extracted data side-by-side) | 8 | 80 |
| 2.9 | Shareable result cards (OG image generation) | 6 | 60 |
| 2.10 | Social share buttons (Twitter, WhatsApp, Facebook) | 3 | 30 |
| | **Phase 2 Subtotal** | **50** | **£500** |

### Phase 3: Real-time, Notifications & Follow System

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 3.1 | Backend: WebSocket/SSE endpoint for live results | 6 | 60 |
| 3.2 | Frontend: live-updating dashboard components | 5 | 50 |
| 3.3 | Backend: User preferences (follow state/candidate) | 5 | 50 |
| 3.4 | Frontend: Follow button + preferences page | 4 | 40 |
| 3.5 | Backend: Web Push notification service | 6 | 60 |
| 3.6 | Frontend: notification bell + opt-in flow | 5 | 50 |
| 3.7 | Backend: notification triggers (new results in followed area) | 4 | 40 |
| | **Phase 3 Subtotal** | **35** | **£350** |

### Phase 4: Analytics & Monitoring

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 4.1 | Backend: Turnout analytics endpoint | 4 | 40 |
| 4.2 | Frontend: Turnout analytics page + demographic charts | 6 | 60 |
| 4.3 | Backend: Election Pulse Index algorithm | 5 | 50 |
| 4.4 | Frontend: Pulse Index breakdown page | 3 | 30 |
| 4.5 | Backend: Incident model + CRUD API | 5 | 50 |
| 4.6 | Frontend: Incident map + list + report form | 8 | 80 |
| 4.7 | Backend: Historical data import + comparison API | 6 | 60 |
| 4.8 | Frontend: Historical comparison page + trend charts | 6 | 60 |
| 4.9 | Competitive state ranking (backend + frontend) | 4 | 40 |
| | **Phase 4 Subtotal** | **47** | **£470** |

### Phase 5: Premium Features

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 5.1 | Backend: AI insights generation (LLM summaries) | 6 | 60 |
| 5.2 | Frontend: Insights feed page + dashboard widget | 5 | 50 |
| 5.3 | Backend: Predictive upload completion | 4 | 40 |
| 5.4 | Frontend: Pending uploads page with ETA | 3 | 30 |
| 5.5 | i18n setup + English base extraction | 5 | 50 |
| 5.6 | Translations integration (Hausa, Yoruba, Igbo, Pidgin) | 6 | 60 |
| 5.7 | PWA: service worker + offline caching + banner | 6 | 60 |
| 5.8 | Voice search (Web Speech API) | 4 | 40 |
| 5.9 | Text-to-speech for results | 3 | 30 |
| 5.10 | Accessibility modes (large text, high contrast) | 4 | 40 |
| 5.11 | PVC collection tracking (backend + frontend) | 6 | 60 |
| | **Phase 5 Subtotal** | **52** | **£520** |

### Testing, QA & Deployment

| # | Task | Hours | Cost (£) |
|---|------|-------|----------|
| 6.1 | Cross-browser + mobile device testing | 6 | 60 |
| 6.2 | Performance audit + optimization | 4 | 40 |
| 6.3 | Accessibility audit (WCAG 2.1 AA) | 4 | 40 |
| 6.4 | Backend testing (new endpoints) | 5 | 50 |
| 6.5 | Production deployment + DNS switch | 3 | 30 |
| 6.6 | Bug fixes from QA | 8 | 80 |
| | **QA Subtotal** | **30** | **£300** |

---

## 4. Total Estimate Summary

| Phase | Hours | Cost (£) |
|-------|-------|----------|
| Phase 1: Core Redesign & Brand | 58 | £580 |
| Phase 2: Map, Results & Verification | 50 | £500 |
| Phase 3: Real-time & Notifications | 35 | £350 |
| Phase 4: Analytics & Monitoring | 47 | £470 |
| Phase 5: Premium Features | 52 | £520 |
| Testing, QA & Deployment | 30 | £300 |
| **TOTAL** | **272** | **£2,720** |

---

## 5. Timeline

| Phase | Duration | Delivery |
|-------|----------|----------|
| Phase 1 | 2 weeks | Weeks 1–2 |
| Phase 2 | 2 weeks | Weeks 3–4 |
| Phase 3 | 1.5 weeks | Weeks 5–6 |
| Phase 4 | 2 weeks | Weeks 6–8 |
| Phase 5 | 2 weeks | Weeks 8–10 |
| QA & Launch | 1 week | Week 11 |
| **Total Timeline** | **~11 weeks** | |

---

## 6. Payment Schedule

| Milestone | Trigger | Amount (£) |
|-----------|---------|------------|
| Deposit | Project kickoff | £500 |
| Milestone 1 | Phase 1 delivered (brand + dashboard redesign on staging) | £580 |
| Milestone 2 | Phase 2 delivered (map + verification + sharing) | £500 |
| Milestone 3 | Phase 3 delivered (real-time + notifications live) | £350 |
| Milestone 4 | Phase 4 + 5 + QA + Launch | £790 |
| **Total** | | **£2,720** |

---

## 7. What's Included

- All source code (client retains full ownership of repository)
- Production deployment to client's VPS
- SSL certificate setup and auto-renewal
- Docker containerization for all services
- Technical documentation (API docs, deployment guide)
- 2 weeks post-launch bug fix support (included)

## 8. What's Not Included

- Domain registration and DNS management (client responsibility)
- VPS hosting costs (client's existing server)
- Google Maps API usage fees (client provides API key)
- OpenAI API costs for AI insights (client provides API key)
- Professional translation services (developer integrates translations provided by client)
- Content creation (copywriting, images, custom illustrations)
- Ongoing maintenance beyond 2-week post-launch window
- Native mobile apps (iOS/Android) — this is a responsive web application
- Legal/compliance review
- Logo design (client provides or approves text-based logo)

---

## 9. Assumptions

1. Client provides timely feedback (within 2 business days per review)
2. Existing VPS infrastructure remains available
3. Client provides API keys (Google Maps, OpenAI)
4. Translation content for Hausa, Yoruba, Igbo, Pidgin provided by client (or machine translation approved)
5. Design direction approved at end of Phase 1 before further phases
6. Historical election data provided by client in structured format
7. No major scope changes after agreement (additions quoted separately at £10/hr)

---

## 10. Acceptance

| | Client | Developer |
|---|--------|-----------|
| Name | | |
| Signature | | |
| Date | | |

---

*This work order is for development services only. Payment is for completed deliverables at the agreed hourly rate of £10/hour. Total project cost: £2,720.*
