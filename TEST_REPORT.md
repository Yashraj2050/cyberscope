# CyberScope Test Report

This report documents the final verification of the CyberScope repository post-cleanup.

## 1. Backend Regression (Python Engine)
- **Command:** `PYTHONPATH=. ./venv/bin/pytest`
- **Total Tests:** 62
- **Passed:** 62
- **Failed:** 0
- **Skipped:** 0
- **Status:** PASS

## 2. Frontend Build (React/Vite)
- **Command:** `cd frontend && npm run build`
- **TypeScript Compilation:** Passed (0 errors)
- **Vite Bundling:** Passed (0 errors)
- **Status:** PASS

## 3. Packaged Application (.app) Verification
The macOS application bundled via Tauri was executed locally in a clean state.

| Test Case | Result | Notes |
| :--- | :--- | :--- |
| Application Launch | **PASS** | App boots and spawns background engine cleanly |
| Scenario Selection | **PASS** | Dropdown fetches scenarios from 127.0.0.1:8000 |
| Run Analysis | **PASS** | Request succeeds, cascading UI updates |
| Telemetry Rendering | **PASS** | Raw events display in chronological order |
| Graph Rendering | **PASS** | Attack graph renders nodes and directed edges |
| Gap Detection | **PASS** | Discovered gaps are highlighted |
| Candidates | **PASS** | Plausible candidates rendered with dynamic support bars |
| Verification | **PASS** | 6-dimension checklist strictly enforced |
| Final Classification | **PASS** | Badges clearly state OBSERVED, INFERRED, or UNKNOWN |
| Export | **PASS** | Reconstructed pipeline exported cleanly (no ground-truth leaked) |
| Exit | **PASS** | Application terminates and reaps PyInstaller daemon cleanly |

All tests successfully executed in an air-gapped environment.
