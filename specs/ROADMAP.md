# Project Roadmap – AJVC Compliance Platform (Phase 2)

_This roadmap captures the high-level phases, milestones and key features for Phase 2 as agreed in the Gantt & planning documents. Dates are indicative and will be kept in sync with the master Gantt._

| Phase       | Feature / Work-stream               | Start     | End       |
| ----------- | ----------------------------------- | --------- | --------- |
| UX          | 🗂️ Document Folder Screens          | 10-Jun-25 | 11-Jun-25 |
| UX          | 🗃️ Portfolio DB Screens             | 10-Jun-25 | 11-Jun-25 |
| Backend     | Phase-2 DB migrations (TRD §§ 9-18) | 10-Jun-25 | 12-Jun-25 |
| Backend     | 🔍 Parse Document Content service   | 17-Jun-25 | 19-Jun-25 |
| Backend     | 💸 Draw-down core service & APIs    | 20-Jun-25 | 23-Jun-25 |
| Backend     | 🏦 Bank-sync service _(PoC)_        | 24-Jun-25 | 27-Jun-25 |
| Backend     | ✉️ Notification Hub & email hooks   | 28-Jun-25 | 29-Jun-25 |
| Backend     | 📤 Unit-Allotment Generator         | 30-Jun-25 | 02-Jul-25 |
| Backend     | 🔄 LP Details update API            | 03-Jul-25 | 04-Jul-25 |
| Backend     | 🏢 Entities API                     | 05-Jul-25 | 06-Jul-25 |
| Backend     | 📊 Fund Details API                 | 07-Jul-25 | 08-Jul-25 |
| Backend     | 📝 SEBI Activity Report Service     | 09-Jul-25 | 10-Jul-25 |
| Backend     | 📑 inVi Filing Pack generator       | 11-Jul-25 | 13-Jul-25 |
| Backend     | 📥 Portfolio Ingestor Service       | 14-Jul-25 | 17-Jul-25 |
| Backend     | 🐳 CI/CD & Infra updates            | 18-Jul-25 | 19-Jul-25 |
| Backend     | ✅ Integration tests > 90 %         | 20-Jul-25 | 22-Jul-25 |
| Backend     | 🐞 Bug-fix & Code-freeze            | 23-Jul-25 | 26-Jul-25 |
| Frontend    | 🌐 Process Page UI                  | 24-Jun-25 | 26-Jun-25 |
| Frontend    | 📄 Capital Call UI                  | 20-Jun-25 | 22-Jun-25 |
| Frontend    | 🏦 LP Draw-down Dashboard           | 23-Jun-25 | 26-Jun-25 |
| Frontend    | 📊 Unit-Allotment Preview           | 27-Jun-25 | 28-Jun-25 |
| Frontend    | 💽 LP Details UI                    | 29-Jun-25 | 30-Jun-25 |
| Frontend    | 📝 SEBI Activity Report UI          | 3-Jul-25  | 5-Jul-25  |
| Frontend    | 📨 inVi Filing UI                   | 4-Jul-25  | 6-Jul-25  |
| Frontend    | 📈 Fund Details Enhancements        | 7-Jul-25  | 7-Jul-25  |
| Frontend    | 🗂 Portfolio DB UI                   | 8-Jul-25  | 11-Jul-25 |
| Frontend    | ⚙ API Integration & Error Handling  | 8-Jul-25  | 12-Jul-25 |
| Frontend    | 🧪 FE Testing (RTL / Cypress)       | 15-Jul-25 | 17-Jul-25 |
| Frontend    | 🎨 UI Bug-fix & Polish              | 18-Jul-25 | 22-Jul-25 |
| Integration | 🔄 End-to-End Testing               | 23-Jul-25 | 25-Jul-25 |
| Integration | 🛡 Performance & Security            | 26-Jul-25 | 27-Jul-25 |
| UAT         | Phase-2 Alpha UAT                   | 28-Jul-25 | 29-Jul-25 |
| UAT         | Beta Launch Fixes                   | 30-Jul-25 | 31-Jul-25 |
| Release     | 🚀 Phase-2 Final Launch             | 1-Aug-25  | 1-Aug-25  |

## Milestones

1. **Code-freeze** – 26 Jul 2025
2. **Alpha-UAT sign-off** – 29 Jul 2025
3. **Beta sign-off** – 31 Jul 2025
4. **Production Launch** – 01 Aug 2025

---

### Next Steps

- Roadmap is Living – PRs updating scope/timeline **must** also update this file.
- Each major feature below will have its own Workplan file under `/specs`.

* UC-LP-1 Generate & Send Capital-Call Notice
* UC-LP-2 Track LP Payment & Reconciliation
* UC-LP-3 Generate Unit-Allotment Sheet
* UC-LP-4 LP Details Update
* UC-SEBI-1 Produce Quarterly SEBI Activity Report
* UC-SEBI-2 Generate inVi Filing Pack
* UC-PORTFOLIO-1 Portfolio Update
