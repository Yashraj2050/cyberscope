# CyberScope

An offline, evidence-aware cybersecurity analysis system that supports SOC assessment by analysing incomplete operational security evidence. It identifies meaningful evidence gaps, reconstructs plausible missing transitions, ranks candidates using available evidence, verifies them with independent checks, and returns OBSERVED, INFERRED, or UNKNOWN to support traceable human supervisory review.

**SIH26157 — Supervisory Analytics Tool for SOC Assessment (SAT-SA)**

## 1. Problem
During a cyberattack, logging systems frequently drop events, adversaries clear logs, or specific sensors simply lack coverage. This leaves investigators with fragmented "islands" of observed activity, making it difficult to understand how an attacker moved from point A to point B. SOC assessment requires a defensible, evidence-based capability to analyse these gaps without overclaiming.

## 2. Solution
CyberScope mathematically evaluates available operational evidence to identify logical gaps. Instead of guessing, it generates plausible candidate hypotheses based on MITRE ATT&CK transitions and rigorously scores them against the surrounding forensic evidence. When the evidence is insufficient, CyberScope explicitly abstains — returning UNKNOWN rather than fabricating a conclusion.

CyberScope complements existing SOC infrastructure (SIEM, EDR, XDR). It does not replace human analysts or examiners. It provides evidence-aware decision support for supervisory assessment.

## 3. Core Pipeline
1. Telemetry parsing
2. Validation
3. Attack graph construction
4. Six-signal evidence gap detection
5. Candidate generation and scoring
6. Independent evidence verification
7. OBSERVED / INFERRED / UNKNOWN classification

## 4. Key Capabilities
- **Evidence Gap Detection:** Identifies discontinuities in operational evidence using six distinct continuity signals.
- **Hypothesis Generation:** Proposes MITRE ATT&CK techniques that logically fit the missing gap.
- **Evidence Verification:** Scores candidates strictly based on surrounding telemetry support — deterministic verification is the final trust boundary.
- **Supervisory Review Support:** Flags UNKNOWN results for human supervisory review, clearly distinguishing observed facts from inference.
- **Air-Gapped Operation:** 100% offline desktop application with zero external API dependencies.

## 5. Architecture
For a deep dive into the algorithmic pipeline, gap signals, and ground-truth isolation, please see [ARCHITECTURE.md](ARCHITECTURE.md).

## 6. Investigation Workflow
The user selects a telemetry scenario. CyberScope renders a chronological attack graph. If an evidence gap is detected, the investigator can inspect the gap to reveal the top candidate hypotheses, their evidence support scores, and the automated verification checks. The system supports traceable supervisory assessment where every conclusion is tied to real evidence.

## 7. Verification States
CyberScope is designed to fail securely. It utilizes three rigid states:
- **OBSERVED:** Directly supported by telemetry.
- **INFERRED:** Candidate is supported by available evidence.
- **UNKNOWN:** Available evidence is insufficient or ambiguous — flagged for human supervisory review.

*Note: The `candidate_score` is an evidence-support score, NOT a probability.*

## 8. Demo Scenarios
The repository includes five synthetic scenarios demonstrating the pipeline's capability to identify credential access, lateral movement, and multi-stage behaviors, as well as its ability to safely halt and report "UNKNOWN" when evidence is ambiguous.

## 9. Offline Design
CyberScope does not require an internet connection. All assets and knowledge bases are bundled locally. The optional local LLM (AI Analyst) provides explanation-only functionality and cannot create evidence, modify telemetry, or override deterministic verification.

## 10. Technology Stack
- **Engine:** Python 3.10, FastAPI, Pytest
- **Frontend:** React, TypeScript, Vite
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
- Organization-wide SOC benchmarking and maturity assessment capabilities.
- Peer and entity comparison for supervisory analytics at scale.

## 17. SIH Context
This repository represents the final submission for SIH26157 (SAT-SA). CyberScope contributes an evidence-aware, offline-first capability to support SOC assessment through traceable evidence analysis and supervisory review.

## 18. License
Licensing decision remains pending.
