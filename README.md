# CyberScope

An offline, evidence-aware cybersecurity investigation system for reconstructing missing transitions in incomplete attack telemetry.

## 1. Problem
During a cyberattack, logging systems frequently drop events, adversaries clear logs, or specific sensors simply lack coverage. This leaves investigators with fragmented "islands" of observed activity, making it difficult to understand how an attacker moved from point A to point B.

## 2. Solution
CyberScope mathematically evaluates the observed telemetry to identify logical gaps. Instead of guessing, it generates plausible candidate hypotheses based on MITRE ATT&CK transitions and rigorously scores them against the surrounding forensic evidence.

## 3. Core Pipeline
1. Telemetry parsing
2. Validation
3. Attack graph construction
4. Gap detection
5. Candidate generation and scoring
6. Evidence verification

## 4. Key Capabilities
- **Gap Detection:** Identifies missing execution chains using six distinct continuity signals.
- **Hypothesis Generation:** Proposes MITRE ATT&CK techniques that logically fit the missing gap.
- **Evidence Verification:** Scores candidates strictly based on surrounding telemetry support.
- **Air-Gapped Operation:** 100% offline desktop application with zero external API dependencies.

## 5. Architecture
For a deep dive into the algorithmic pipeline, gap signals, and ground-truth isolation, please see [ARCHITECTURE.md](ARCHITECTURE.md).

## 6. Investigation Workflow
The user selects a telemetry scenario. CyberScope renders a chronological attack graph. If a gap is detected, the investigator can click the gap to reveal the top candidate hypotheses, their evidence support scores, and the automated verification checks.

## 7. Verification States
CyberScope is designed to fail securely. It utilizes three rigid states:
- **OBSERVED:** Directly supported by telemetry.
- **INFERRED:** Candidate is supported by available evidence.
- **UNKNOWN:** Available evidence is insufficient or ambiguous.

*Note: The `candidate_score` is an evidence-support score, NOT a probability.*

## 8. Demo Scenarios
The repository includes five synthetic scenarios demonstrating the pipeline's capability to identify credential access, lateral movement, and multi-stage behaviors, as well as its ability to safely halt and report "UNKNOWN" when evidence is ambiguous.

## 9. Offline Design
CyberScope does not require an internet connection. It does not use LLMs, cloud AI, or external CDNs. All assets and knowledge bases are bundled locally.

## 10. Technology Stack
- **Engine:** Python 3.10, FastAPI, Pytest
- **Frontend:** React, TypeScript, Vite, TailwindCSS
- **Desktop Packaging:** Tauri (Rust), PyInstaller

## 11. Installation & Running Locally (Development)

**Requirements:** Python 3.10+, Node.js, npm.

```bash
# 1. Setup Backend
cd engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn main:app --port 8000

# 2. Setup Frontend (in a new terminal)
cd frontend
npm install
npm run dev
```

## 12. Building Desktop Application (Release)
```bash
# Bundle Backend
cd engine
pyinstaller --name engine --onefile --add-data "datasets/demo/*.json:datasets/demo" main.py
cp dist/engine ../src-tauri/bin/engine-aarch64-apple-darwin

# Build Tauri Application
cd frontend
npm run build
cd ../src-tauri
npx @tauri-apps/cli build
```

## 13. Testing
To run the automated test suite:
```bash
cd engine
PYTHONPATH=. ./venv/bin/pytest
```

## 14. Project Structure
- `engine/`: Python reconstruction pipeline and FastAPI server.
- `frontend/`: React Vite application.
- `src-tauri/`: Rust desktop wrapper and sidecar configuration.
- `datasets/`: Synthetic evaluation scenarios.

## 15. Limitations
- Uses a hardcoded, deterministic transition knowledge base (no dynamic threat intelligence ingestion).
- Uses synthetic demo telemetry (not validated against real-world, large-scale noisy enterprise SIEM data).
- The attack graph rendering library may experience performance degradation with extremely large topographies (100+ nodes).
- Windows packaging is provided through the reproducible CI workflow and must be built on a Windows runner (no native Windows binary is currently committed).

## 16. Future Work
- Ingesting arbitrary STIX/JSON logs from external SIEMs.
- Expanding the localized MITRE ATT&CK transition mapping.

## 17. SIH Context
This repository represents the final Milestone 10 submission for the SIH hackathon. It has been strictly frozen, audited, and verified to run in completely offline, air-gapped environments.

## 18. License
Licensing decision remains pending.
