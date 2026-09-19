<br>

<div align="left">
  <h1>CYBERSCOPE</h1>
  <p style="font-family: monospace; letter-spacing: 1px; color: #8b949e;">OFFLINE SECURITY ANALYSIS</p>
  <p>Localized desktop application for offline analysis of structured cybersecurity events, attack-graph reconstruction, and machine-learning-based reconstruction-gap scoring.</p>
</div>

<br>
<br>

---

<br>

| Capability | Status |
|---|---|
| Structured security event ingestion | Implemented |
| Attack graph generation | Implemented |
| Reconstruction-gap detection | Implemented |
| ML candidate scoring | Implemented |
| Local ML inference | Implemented |
| Live packet capture | Not implemented |
| Active network reconnaissance | Not implemented |
| Endpoint monitoring | Not implemented |
| Local LLM analysis | Experimental / Stubbed |
| Persistent security-case database | Not implemented |

## Overview

Security investigations often involve incomplete or fragmented event sequences. CyberScope works with structured security events and reconstructs an attack graph, identifies potential gaps, and ranks candidate missing events. 

The system relies entirely on the offline ingestion of static JSON scenario datasets and does not collect, intercept, or analyze live network traffic.

## Architecture

```text
Structured Security Events
        │
        ▼
Next.js Frontend
        │
        │ HTTP
        ▼
Tauri Desktop Shell
        │
        │ Python sidecar
        ▼
FastAPI Analysis Engine
        │
        ├── Event ingestion
        ├── Attack graph generation
        ├── Reconstruction-gap detection
        └── ML candidate scoring
                    │
                    ▼
             ranker_model.joblib
             Local Scikit-Learn
```

## Core Workflows

### 01 — Event Ingestion
Parses static, pre-recorded structured JSON scenario datasets into memory.

### 02 — Attack Graph Generation
Converts ingested cyber events into a deterministic `networkx` node/edge attack graph representing relationships and event sequences within the supplied security scenario.

### 03 — Reconstruction-Gap Detection
The reconstruction pipeline analyzes the supplied event graph to identify structural gaps where an expected event may be absent from the available telemetry.

The output represents candidate reconstruction gaps, not confirmed attacker activity.

### 04 — Candidate Scoring
For each detected reconstruction gap, the scoring pipeline extracts structured event features and passes them to the locally stored Scikit-Learn model at:

`engine/ml/models/ranker_model.joblib`

The model produces probability scores used to rank candidate missing events.

## FastAPI Engine

The backend executes via a Python sidecar. The FastAPI service currently exposes its endpoints without JWT or token authentication. It is designed as a local sidecar within the desktop application architecture.

| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| GET | `/health` | Engine status check | Implemented |
| GET/POST | `/api/v1/cases` | CRUD operations for investigation cases | Implemented |
| GET/POST | `/api/v1/events` | Ingestion of structured event data | Implemented |
| GET/POST | `/api/v1/graph` | Attack graph payload for visualization | Implemented |
| GET | `/api/v1/llm/status` | LLM availability/status | Experimental |
| POST | `/api/v1/investigations/{case_id}/ai/explain` | Investigation explanation endpoint | Experimental / Stubbed |

## Machine Learning

CyberScope currently uses classical machine learning for reconstruction-gap candidate ranking.

- **Framework:** Scikit-Learn
- **Model artifact:** `engine/ml/models/ranker_model.joblib`
- **Serialization:** joblib
- **Inference:** Local
- **Input:** Structured cybersecurity event features
- **Output:** Candidate probability scores

## Tauri Layer

The Rust/Tauri layer acts exclusively as a process manager. It uses `tauri_plugin_shell` to spawn the Python FastAPI engine as a background sidecar. No direct OS-level hooks, packet sniffers, or eBPF modules are implemented in the Rust layer.

## Security Analysis Boundary

CyberScope analyzes supplied structured event data. It does not currently collect live telemetry or establish ground truth about an active incident.

Its reconstruction-gap output should therefore be interpreted as candidate analysis over the supplied scenario rather than confirmation of malicious activity.

## Data & Storage

The current security-analysis engine uses in-memory state together with static JSON scenario datasets under `engine/datasets/`.

The frontend contains a Prisma/SQLite schema with `User` and `Post` models, but this schema is not a specialized persistence layer for investigations, events, or attack graphs.

## Limitations

- **No Active Reconnaissance:** CyberScope does not execute live network scanning, port scanning, or endpoint packet capture.
- **Experimental Features:** The LLM explanation features remain stubbed without core implementation files.

## Testing

The Python engine includes pytest-based unit tests covering core analysis and candidate-scoring behavior.

## Project Structure

```text
cyberscope/
├── cyberscope-web/        # Next.js Frontend
├── engine/                # FastAPI Python Backend
│   ├── api/
│   ├── datasets/
│   ├── ml/models/
│   └── tests/
└── src-tauri/             # Rust Desktop Shell
```

## Setup

### Engine
```bash
cd engine
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd cyberscope-web
npm install
npm run dev
```

### Desktop
```bash
cd src-tauri
cargo tauri dev
```
