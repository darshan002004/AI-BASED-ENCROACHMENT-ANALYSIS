# EncroWatch AI: AI-Powered Urban Accessibility and Road & Footpath Encroachment Monitoring System

> **“Cleaner Footpaths. Safer Roads. Smarter Cities.”**  
> *Production-Style MCA Major Project | Smart Cities & Urban Mobility Initiative*

---

## 🏛️ Executive Summary

**EncroWatch AI** is a modern, enterprise-grade Smart City SaaS and GIS platform designed to detect, analyze, map, and resolve road and footpath encroachments using advanced Computer Vision and geometric spatial analysis. 

Rather than functioning as a standard CRUD application or a generic YOLO bounding box demo, EncroWatch AI implements a full **Spatial Encroachment Analysis Engine**:
1. **Semantic Road & Footpath Segmentation**: Segments street scenes into distinct zones (Footpath = Green, Road = Blue, Obstruction = Red, Other = Yellow).
2. **Context-Aware Encroachment Reasoning**: Differentiates legitimate road traffic from pedestrian sidewalk blockages (e.g., a car on the road is normal; a car on a footpath is an illegal encroachment; a vendor blocking a pedestrian corridor triggers high severity).
3. **Footpath Accessibility Scoring ($0–100\%$)**: Mathematically computes total footpath area ($m^2$), occupied area ($m^2$), free walkway space, remaining clearance width, and flags specific accessibility hazards (blocked wheelchair ramps, blocked tactile paving).
4. **Persistent Video Tracking**: Tracks stationary obstacles across video frames over time, distinguishing temporary movements (passing pedestrians) from prolonged persistent barriers.
5. **Spatial-Temporal Duplicate Clustering**: Automatically merges proximate citizen reports within a 60-meter radius into a single master incident with supporting citizen endorsements.
6. **Before / After AI Resolution Verification**: Validates field officer clearance by re-evaluating post-inspection photos using computer vision to verify physical removal before resolving an incident.
7. **Interactive GIS Mapping & Hotspot Density Rankings**: Displays real-time geocoded pins across city wards (MG Road, Indiranagar, BTM Layout, Koramangala, JP Nagar) with live status tracking.
8. **Diurnal Temporal Analytics & PDF Report Generation**: Provides time-of-day (Morning, Afternoon, Evening, Night) and day-of-week incident frequency patterns with instant PDF audit generation via ReportLab.

---

## 🎨 UI Blueprint Design Fidelity

The platform user interface faithfully reproduces the smart-city control dashboard specified in the project blueprint:
- **Left Sidebar**: Dark Navy (`#0F172A`), clean typography, active blue highlight pills, role switcher, and city skyline watermark (*"Smart Cities Start with Walkable Streets"*).
- **KPI Summary Cards**: Total Incidents (`1,248`), Verified (`746`), Pending (`321`), High Severity (`186`), and Avg. Accessibility Score (`68%`).
- **Encroachment Map**: Interactive Leaflet map with high-resolution severity markers (Red = High, Orange = Medium, Green = Low).
- **Recent Incidents Table**: Live thumbnail previews, ward locations, encroachment types, severity badges, and status indicators.
- **Visual Analytics**: Encroachment Types Donut Chart (Vehicles 38%, Vendors 24%, Shop Extensions 16%, Construction 12%, Garbage 6%, Others 4%), Monthly Trend Line Chart, and Top Affected Areas Horizontal Bar Chart.
- **AI Detection Panel**: Real-time side-by-side display of Original Image $\rightarrow$ Segmented Detection Output $\rightarrow$ Dimensional Analysis Result with downloadable PDF report and latency badge (*"AI analysis completed in 2.3 seconds"*).

---

## 🛠️ Technology Stack

| Component | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS v4, Lucide React, Recharts, Leaflet, React-Leaflet, Axios |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt), WebSockets |
| **Computer Vision / AI** | OpenCV (cv2), NumPy, Shapely (Spatial Polygons), PIL (Pillow), Modular YOLO Hooks |
| **Database** | MongoDB (Motor async driver) with automatic local resilient document store fallback |
| **Document Export** | ReportLab (PDF generation) & native CSV Streaming |
| **DevOps & Containers**| Docker, Multi-Stage Dockerfile, Nginx Reverse Proxy, Docker Compose |

---

## 👤 User Roles & Workflows

### 1. Citizen (`citizen@encrowatch.ai` / `citizen123`)
- Mobile-first report submission interface.
- Upload photos/videos or capture live evidence using device camera.
- One-click GPS geolocation auto-detection (with ward selector fallback).
- Real-time **AI Pre-Analysis**: automatically suggests obstacle category and confidence before submission.
- Track submitted incidents across lifecycle stages: `Pending` $\rightarrow$ `AI Review` $\rightarrow$ `Verified` $\rightarrow$ `Assigned` $\rightarrow$ `Resolved`.

### 2. Field Officer (`officer@encrowatch.ai` / `officer123`)
- Dedicated Officer Hub and assigned patrol incident queue.
- Review GPS location, original evidence, and severity warnings.
- Upload on-site field inspection photo after clearing obstruction.
- Trigger automated **Before/After AI Verification** to prove clearance.
- Submit inspection observations and sign off on verified resolutions.

### 3. Administrator (`admin@encrowatch.ai` / `admin123`)
- Full smart city control dashboard matching the project design blueprint.
- Incident lifecycle management: verify AI findings, adjust severity, and assign officers.
- AI Detection Playground: live testing of segmentation overlays and video persistence tracking.
- Interactive GIS Map with filters by severity, type, status, and ward.
- Advanced Analytics: diurnal time-of-day patterns and day-of-week recurrence trends.
- Hotspot density analysis and ranked municipal ward league table.
- Generate and download formal PDF Audit Dossiers and raw CSV datasets.
- System configuration: tune accessibility tolerance (default 1.5m), confidence cutoff, and duplicate radius.

---

## 🚀 Quick Start Guide

### Option A: Local Development (Recommended for Testing & Viva)

#### 1. Backend Setup
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The backend automatically connects to local MongoDB on port 27017 (or seamlessly falls back to embedded document storage if MongoDB is offline), pre-seeding all demo users, incidents, and notifications.*

#### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open **`http://localhost:5173`** in your browser!

---

### Option B: Local Docker Compose (Development)

To build and run the development containerized stack:
```bash
docker compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`
- MongoDB Port: `127.0.0.1:27017`

---

### Option C: Hardened Production Docker Deployment

To build and run the production-grade stack with isolated internal networking, resource limits, healthchecks, and Nginx reverse proxy:

```bash
# 1. Generate strong production secret key
python scripts/generate_secret_key.py

# 2. Configure .env with your production values (refer to .env.example)
cp .env.example .env

# 3. Launch hardened production containers
docker compose -f docker-compose.prod.yml up -d --build
```
- Ingress (Nginx Web + Reverse Proxy): `http://localhost:80`
- Direct access to MongoDB and Backend is blocked from external networks for security.

---

## 📚 Production & Operations Guides

For comprehensive enterprise deployment, security governance, and disaster recovery procedures, consult the operational runbooks:

- [🚀 Production Deployment Runbook (DEPLOYMENT.md)](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/DEPLOYMENT.md): Container specs, Nginx reverse proxy, resource limits, migration guides, and cloud options.
- [🛡️ Security Governance & Hardening (SECURITY.md)](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/SECURITY.md): JWT RS256/HS256, bcrypt password hashing, RBAC enforcement, magic-byte upload validation, rate limiting, and PII audit logging.
- [💾 Backup & Disaster Recovery Guide (BACKUP_RESTORE.md)](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/BACKUP_RESTORE.md): Automated MongoDB snapshots, isolated sandbox test restore validation, media volume backups, and recovery SLA metrics.

---

## 🔑 Pre-Seeded Demo Credentials

For demonstration, evaluation, and university viva presentations, one-click persona switcher buttons are available directly on the login screen and sidebar:

| Role | Email | Password | Assigned Scope |
| :--- | :--- | :--- | :--- |
| **👑 Admin** | `admin@encrowatch.ai` | `admin123` | Central Command / All Wards |
| **👮 Field Officer** | `officer@encrowatch.ai` | `officer123` | Central Ward / MG Road Corridor |
| **👮 Field Officer 2** | `priya.officer@encrowatch.ai` | `officer123` | East Ward / Indiranagar Corridor |
| **🚶 Citizen** | `citizen@encrowatch.ai` | `citizen123` | Civic Contributor / BTM Layout |

---

## 📡 Key REST API Endpoints

- `POST /api/auth/login` — User authentication and JWT generation
- `POST /api/auth/demo-switch/{role}` — One-click demo role switcher
- `GET /api/incidents` — Filtered list of incidents (search, severity, type, status, pagination)
- `POST /api/incidents` — Create incident with automatic spatial duplicate clustering
- `GET /api/incidents/{id}` — Full incident dossier with timeline and detection geometry
- `POST /api/incidents/{id}/inspect` — Officer inspection photo submission
- `POST /api/incidents/{id}/verify-resolution` — Automated Before/After AI Resolution Verification
- `POST /api/ai/analyze` — Standalone computer vision detection & segmentation
- `POST /api/ai/track-video` — Persistent video encroachment duration tracking
- `GET /api/analytics/kpis` — Dashboard KPI metrics
- `GET /api/analytics/time-of-day` — Diurnal distribution (Morning, Afternoon, Evening, Night)
- `GET /api/reports/pdf/incident/{id}` — Download formal ReportLab PDF audit
- `GET /api/reports/csv` — Export complete incident dataset in CSV format
- `WS /ws/notifications` — Live WebSocket broadcast of new reports and resolution events

---

## 🎓 Viva Presentation & Examiner Talking Points

When presenting this project to evaluators and professors:
1. **Beyond Basic YOLO**: Emphasize that EncroWatch AI does not simply label bounding boxes. It implements a **Spatial Encroachment Analysis Engine** using polygon intersection geometry to distinguish legitimate road usage from pedestrian footpath blockages.
2. **Quantifiable Metrics**: Highlight that the Footpath Accessibility Score ($0-100\%$) and Occupancy Percentage are calculated from measurable dimensional geometry (IRC-103 standards) rather than arbitrary random numbers.
3. **Temporal Video Tracking**: Explain how temporal persistence tracking distinguishes temporary movements (pedestrians walking past or cars at signals) from stationary unauthorized stalls lasting $>3$ seconds.
4. **Before/After AI Verification**: Demonstrate how the platform closes the loop on civic complaints by executing an AI comparison between original evidence and officer inspection photos to mathematically prove that the obstruction was cleared before marking the incident as resolved.
5. **Architectural Resilience**: Point out that the system utilizes asynchronous MongoDB via Motor with an automatic local fallback store, ensuring zero-setup demonstration reliability on any presentation machine.
