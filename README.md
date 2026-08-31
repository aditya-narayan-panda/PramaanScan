# PramaanScan — National Cryptographic Authenticity & Media Provenance Platform

**PramaanScan** is an end-to-end multi-tenant digital provenance, cryptographic verification, and multimodal forensic analysis platform designed for national institutions, government bodies, universities, and regulatory authorities.

---

## Key Highlights & Innovations

1. **Authoritative Cryptographic Authenticity**:
   - **Ed25519** asymmetric digital signatures + SHA-256 content hashing.
   - Server-side signing and key generation: Private keys are encrypted at rest and **never exposed via the API**.
   - Zero cryptographic burden on institutional officers: Upload document + metadata $\rightarrow$ automatic signing + instant QR provenance issuance.

2. **Multimodal Forensic Advisory Pipeline**:
   - AI/ML pipelines for Document Text Forensics, Image Tampering Detection, Audio Deepfake Detection, and Video Frame Analysis.
   - Clear architectural boundary: Cryptographic verification is **authoritative** (mathematically deterministic); ML analysis is strictly **secondary/advisory**.

3. **Multi-Tenant Authority Boundaries (Hardened Role-Based Access Control)**:
   - Authorities strictly scoped to their registered institution ($403\text{ Forbidden}$ enforced at API level for all cross-tenant access attempts).
   - Institution suspension immediately blocks authority login and runtime token access.
   - Separation of Access vs. Refresh tokens with token type verification.
   - JTI-based refresh token revocation table: Server-side invalidation on logout prevents replay attacks.

4. **Public Zero-Barrier Verification**:
   - Instant verification via Document File Upload, SHA-256 Hash query, or QR Code scan.
   - Scanned QR codes redirect directly to human-readable verification portals (`/verify/communication/{id}`).
   - Privacy-preserving append-only verification logging with SHA-256 hashed IP and User-Agent headers.

---

## System Architecture

```
                                    +-----------------------------------------+
                                    |         PramaanScan Frontend UI         |
                                    |  (React 18 + TypeScript + Tailwind CSS) |
                                    +--------------------+--------------------+
                                                         |
                                                 REST / JSON (JWT)
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |          FastAPI Backend Engine         |
                                    |            (Uvicorn / Python)           |
                                    +----+--------------------+----------+----+
                                         |                    |          |
                   +---------------------+                    |          +----------------------+
                   v                                          v                                 v
   +-------------------------------+          +-------------------------------+    +---------------------------+
   |   Ed25519 Cryptographic Core  |          |       Multimodal ML Core      |    |      Relational DB        |
   | - In-Memory Key Custody       |          | - Document Text Classifier    |    | (SQLAlchemy / SQLite / PG)|
   | - SHA-256 Provenance Ledger   |          | - Image Forensics (ResNet)    |    | - Users & Issuers         |
   | - Key Revocation Subsystem    |          | - Audio Deepfake (Wav2Vec2)   |    | - Keys & Communications   |
   | - QR Code Generator Engine    |          | - Video Frame Temporal Model  |    | - Revoked Tokens (JTI)    |
   +-------------------------------+          +-------------------------------+    | - Audit & Verify Logs     |
                                                                                   +---------------------------+
```

---

## Installation & Quickstart Guide

### 1. Python Environment & Dependency Installation

#### Target Python Version: **Python 3.12** (Supports full TensorFlow 2.16.2 / Keras 3 / Media Forensics stack)

##### One-Click Setup (Windows):
```cmd
setup_env.bat
```

##### Manual Setup:
```bash
# Clone or navigate to the repository
cd pramaanscan

# Create and activate Python 3.12 virtual environment
py -3.12 -m venv .venv --system-site-packages
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 1. Install Backend Dependencies
pip install -r backend_final/requirements-backend.txt

# 2. Install Multimodal ML Subsystem Requirements
pip install -r PramaanScan_ML/requirements.txt
```


### 2. Database Initialization & Seeding

```bash
cd backend_final

# 1. Initialize Database Schema
python create_db.py

# 2. Seed Comprehensive Demo Data (Institutions, Ed25519 Keys, Sample Signed Docs)
python seed_db.py

# 3. Start the Backend Server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Run Backend Automated QA Test Suite

```bash
cd backend_final
python test_suite.py
```
*Validates all 8 core security and cryptographic requirements (100% automated pass).*

### 3. Frontend Setup & Startup

```bash
cd pramaanscan-frontend/frontend

# 1. Install packages
npm install

# 2. Run Vite development server
npm run dev
```
*Access UI at `http://localhost:5173`.*

---

## Demo Accounts (Pre-Seeded)

| Portal | Email | Password | Role / Institution |
|---|---|---|---|
| **System Admin** | `admin@pramaanscan.gov.in` | `Admin@12345` | Platform Administrator |
| **Institution Authority** | `officer@nta.ac.in` | `Nta@12345` | National Testing Agency (NTA) |
| **Institution Authority** | `director@meity.gov.in` | `Meity@12345` | Ministry of Electronics & IT (MeitY) |
| **Institution Authority** | `dean.academics@iitb.ac.in` | `Iitb@12345` | IIT Bombay |
| **Suspended Institution** | `authority@suspended-test.org` | `Suspended@12345` | Suspended Academy (Tests 403) |

---

## Verification Test Cases

1. **Valid Document Verification**:
   - Query Communication ID: `nta_jee_main_2026_notice` or `meity_digital_trust_circular_2026`
   - Result: `VERIFIED` with full cryptographic provenance.

2. **Tampered Document Verification**:
   - Upload any document modified after issuance.
   - Result: `UNSIGNED` / `MODIFIED` (Cryptographic mismatch flagged immediately).

3. **Revoked Signing Key Verification**:
   - Query Key: `key_nta_legacy_revoked_2025`
   - Result: `REVOKED` with audit reason and revocation timestamp.

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Radix UI, Lucide React, Framer Motion, TanStack Query, Recharts, QR Scanner / QR Code generator.
- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, Cryptography (Ed25519), Uvicorn.
- **ML / AI**: Scikit-learn, PyTorch, Librosa, OpenCV, PyPDF.
