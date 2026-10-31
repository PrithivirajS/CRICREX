# CRICREX — MVP proposal

## Product direction
One responsive platform where a captain creates a match and coordinates team, ground, opponent, umpire, scorer and status. Start with a web MVP; reuse the backend for later Android/iOS apps.

## Proposed stack
- UI: responsive HTML5, CSS3, JavaScript; React can be a phase-two option if desired.
- Backend: Python Flask REST API, SQLAlchemy + Alembic migrations.
- Database: MySQL 8 managed database (SQLite is used only in the included local prototype).
- Authentication: secure password hashing, role-based permissions, email verification and password reset.
- Media: S3-compatible object storage for team logos and ground photos.
- Maps/search: Google Maps Platform or Mapbox, with location-radius search.
- Notifications: transactional email first; SMS/WhatsApp provider later, with consent and delivery logs.
- Payments: Razorpay or PayU after payment, cancellation, refund and platform-fee rules are agreed.
- Hosting: AWS Lightsail/EC2 or equivalent, HTTPS, managed database, backups, error monitoring and uptime alerts.

## MVP scope
1. Captain/player accounts and team profiles.
2. Ground-owner profiles, ground listings, rates and booking request flow.
3. Open match creation and opponent discovery/request/approval.
4. Umpire and scorer profiles, search and booking request/approval.
5. Match coordination page with status, fee and participants.
6. Basic dashboard for captains, owners and officials; simple admin management.
7. Responsive UI, smoke tests, deployment and handover documentation.

## Indicative timeline
| Phase | Duration | Deliverables |
|---|---:|---|
| Discovery & UX | 1 week | User flows, screen designs, requirements and acceptance criteria |
| Core platform | 1–2 weeks | Auth, roles, teams, ground and official profiles |
| Match coordination | 2 weeks | Match creation, opponent requests, booking statuses and match detail |
| QA, deployment & handover | 1–2 weeks | Responsive testing, security baseline, deployment and training |
| **Total** | **6–8 weeks** | MVP release, assuming timely decisions and feedback |

## Indicative development cost (India, INR)
These are planning estimates, not a vendor quote; taxes and third-party charges may be extra.

| Workstream | Estimate |
|---|---:|
| UX/UI design and clickable flows | ₹40,000–₹70,000 |
| Responsive frontend | ₹80,000–₹1,20,000 |
| Backend, roles and database | ₹1,00,000–₹1,50,000 |
| Match, opponent, ground and official workflows | ₹1,20,000–₹1,80,000 |
| QA, security baseline, deployment and handover | ₹40,000–₹70,000 |
| **Estimated MVP total** | **₹3,80,000–₹5,90,000** |

A lean solo-developer build can sometimes be scoped lower (around ₹2.5–₹3.5 lakh) by limiting admin tooling, notifications and polish. The production scope above is the safer planning band. The included code is a starter prototype, not the finished production MVP.

## Hosting and recurring costs
| Item | Planning estimate / month |
|---|---:|
| Small app server / compute | ₹1,500–₹5,000 |
| Managed database + backups | ₹1,500–₹5,000 |
| Storage, email, logs and monitoring | ₹500–₹3,000 |
| Domain (annualized) | ₹100–₹200 |
| **Typical early-stage infrastructure** | **₹3,600–₹13,200/month** |

Traffic, image storage, map API use, SMS/WhatsApp, payment gateway charges, taxes and production redundancy can increase costs. A minimal single-server deployment can be cheaper but has more operational risk.

## Ongoing maintenance
- Basic maintenance/support: ₹15,000–₹30,000/month for bug fixes, dependency updates, backups/health checks and a small support allowance.
- Active enhancement/support: ₹30,000–₹60,000/month depending on SLA and feature velocity.
- Payment gateway charges and usage-based messaging/maps are separate.

## Phased roadmap
- **Phase 1 — MVP:** accounts, teams, grounds, open matches, opponent approval, umpire/scorer discovery, booking statuses, responsive dashboards.
- **Phase 2 — Operational readiness:** ground calendar and slot locking, payment gateway, automated notifications, cancellations/refunds, reviews, admin moderation, reports, audit trail and stronger abuse prevention.
- **Phase 3 — Scale:** Android/iOS apps, live scoring integrations, advanced location recommendations, memberships, tournaments and analytics.

## Key assumptions / exclusions
- Single-city pilot first; multi-city operations and complex tax/accounting are not in MVP.
- Fees are estimates and should be confirmed after user-flow sign-off and a detailed statement of work.
- Online payments are planned as a later phase, not enabled in the prototype.
- Final schedule depends on availability of product decisions, test users and payment/maps provider accounts.
