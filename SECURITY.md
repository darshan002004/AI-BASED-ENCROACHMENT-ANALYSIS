# EncroWatch AI — Production Security & Governance Specification

> **Municipal Infrastructure & Urban Intelligence Security Policy**  
> Covers authentication, role isolation, data privacy, and cryptographic auditability.

---

## 1. Security Architecture & Threat Model

EncroWatch AI is engineered with defense-in-depth security principles to safeguard municipal operations against unauthorized access, privilege escalation, data tampering, and citizen privacy exposure.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Perimeter Defense: Nginx Security Headers & Rate Limiters                │
│    - HSTS, X-Content-Type-Options, X-Frame-Options, Permissions-Policy      │
│    - Endpoint-specific IP rate limiting (5 req/min on login, 10 on AI)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Cryptographic Authentication & Role-Based Access Control (RBAC)          │
│    - HS256 signed JWT tokens with 256-bit secret keys                       │
│    - Passwords hashed with bcrypt (cost factor 12)                          │
│    - Strict separation of Admin, Officer, and Citizen roles                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Application Security & Input Validation                                   │
│    - Pydantic v2 strict schema validation                                   │
│    - File upload magic-byte verification (JPEG, PNG, WebP, MP4)             │
│    - UUID-based sanitized storage (immune to path traversal ../ attacks)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. Privacy Anonymization & Cryptographic Audit Trails                       │
│    - Automated Haar-Cascade / YuNet face and license plate redaction        │
│    - 100% PII stripping on all unauthenticated Public Transparency endpoints│
│    - SHA-256 tamper-evident cryptographic hash chaining for all audit logs  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication & JWT Token Management

### Password Security:
- Passwords are encrypted using **bcrypt** with a work factor of 12 rounds via `passlib[bcrypt]`.
- Raw passwords are never stored in memory longer than necessary for authentication and are never logged.

### JWT Token Issuance & Signing:
- Tokens are signed using **HMAC-SHA256 (HS256)**.
- `SECRET_KEY` must be at least 32 characters (256 bits of entropy) in production; startup environment validation aborts initialization if default or weak keys are detected.
- Standard production token expiration is **1,440 minutes (24 hours)**.

### Session Invalidation & Protection:
- Any `401 Unauthorized` response immediately purges tokens from client `localStorage`.
- Tampered token payloads (e.g. altering the role claim from citizen to admin) fail HMAC signature verification on the server and trigger an immediate `401 Unauthorized`.

---

## 3. Role-Based Access Control (RBAC)

The system enforces three distinct, immutable authorization roles:

| Role | Permitted Capabilities | Prohibited Capabilities |
| :--- | :--- | :--- |
| **`admin`** | Full municipal oversight, officer approval & rejection, SLA configuration, audit trail inspection, model registry governance, user management. | None. |
| **`officer`** | View assigned cases, review AI computer vision detections, conduct field inspections, submit clearance evidence. | Accessing admin user rosters, modifying SLA rules, approving other officers, viewing audit chain integrity. |
| **`citizen`** | Report new sidewalk encroachments, track own reported incidents (`my_reports=true`), view public transparency map, submit feedback. | Accessing officer review queues, viewing other citizens' private reports, accessing admin or officer APIs. |

### Officer Registration Gate:
- Public officer registration creates accounts in `pending_approval` status (`is_active: false`).
- Pending officers **cannot** log in (returns `HTTP 403 Forbidden`).
- Rejected officers **cannot** log in (returns `HTTP 403 Forbidden` with the documented rejection reason).
- Deactivated officers are blocked immediately from all operational endpoints.

---

## 4. Input & File Upload Security

### Magic-Byte Content Verification:
All uploaded evidence is inspected at the binary level using `validate_file_content_and_type()` in `backend/app/utils/security.py`:
- Disguised executable files (e.g., `.exe` renamed to `.jpg`) are detected and rejected.
- Permitted image formats: JPEG (`\xff\xd8\xff`), PNG (`\x89PNG\r\n\x1a\n`), WebP (`RIFF...WEBP`).
- Permitted video formats: MP4 (`ftyp`).

### Path Traversal Protection:
- Original file names submitted by clients are discarded for storage paths.
- All stored files are given UUIDv4-based names (`upload_` + `uuid.uuid4().hex` + `.ext`) and placed in designated subdirectories (`/uploads/original/`, `/uploads/annotated/`, `/uploads/privacy/`).
- Attempts to inject relative paths (`../../etc/passwd`) are completely neutralized.

### File Size Limits:
- Images: Maximum **25 MB**.
- Videos: Maximum **50 MB**.
- Requests exceeding these limits receive `HTTP 413 Request Entity Too Large`.

---

## 5. Rate Limiting & DoS Protection

In-memory rate limiters in `backend/app/main.py` throttle requests per client IP:
- **Authentication (`/api/auth/login`):** Maximum **5 requests per minute** to prevent brute-force attacks.
- **AI Computer Vision (`/api/ai/`):** Maximum **10 requests per minute** to protect CPU resources.
- **General APIs (`/api/`):** Maximum **60 requests per minute**.

---

## 6. Citizen Privacy & Public Transparency

- **Automated Anonymization:** Computer vision models detect faces and vehicle registration plates in uploaded evidence, applying Gaussian blurring before saving to the `/uploads/privacy/` partition.
- **100% PII Redaction:** The Public Transparency API (`GET /api/public/incidents`) strictly strips `reporter_name`, `reporter_id`, `reporter_phone`, and internal officer comments, serving only anonymized imagery and macro-level coordinates.

---

## 7. Cryptographic Audit Chain Integrity

Every administrative decision (officer approval, officer rejection, status modification, SLA escalation) is recorded in the `audit_logs` collection:
- Each record computes a SHA-256 hash chaining to the `prev_hash` of the preceding record:
  $$\text{record\_hash} = \text{SHA256}(\text{prev\_hash} + \text{action} + \text{actor} + \text{target} + \text{timestamp} + \text{details})$$
- The root record is bound to `GENESIS_HASH`.
- An administrator can run `/api/audit/verify-integrity` at any time to mathematically prove that no audit records have been altered, inserted, or deleted.

---

## 8. Production Security Checklist

- [x] Change default `SECRET_KEY` to a random 64-character hex string.
- [x] Confirm `ENVIRONMENT=production` in `.env`.
- [x] Confirm `ALLOW_DEMO_SWITCH=false` and `ALLOW_DEMO_MODE=false`.
- [x] Configure explicit `CORS_ORIGINS` (no wildcards `*`).
- [x] Run containers as non-root user (`encrowatch:1001`).
- [x] Restrict MongoDB port `27017` to internal Docker network.
- [x] Enable SSL/TLS termination on Nginx or cloud load balancer.
- [x] Run `python backend/uat_complete_suite.py` to verify all security controls.
