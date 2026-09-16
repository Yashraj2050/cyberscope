# CyberScope Packaging Guide

This document outlines the architecture and procedure for building the distributable offline desktop application.

## 1. Architecture
CyberScope uses a **Tauri (Rust)** application wrapping a **Vite + React** frontend. It bundles a pre-compiled **FastAPI (Python)** backend via PyInstaller, which is executed as a Tauri "Sidecar".
When the Tauri application launches, the sidecar spawns the local Python backend on `127.0.0.1:8000`. Tauri automatically cleans up the sidecar process on exit.

## 2. Python Backend Packaging
The Python application relies on `uvicorn` and `fastapi`. To create an offline, self-contained executable, `pyinstaller` is used.

## 3. PyInstaller Command
```bash
cd engine
./venv/bin/pyinstaller --name engine --onefile --add-data "datasets/demo/*.json:datasets/demo" main.py
```
This produces the executable in `engine/dist/engine`.
The resulting binary must be copied to `src-tauri/bin/engine-<target-triple>` (e.g. `engine-aarch64-apple-darwin`).

## 4. Tauri Packaging Command
The build process invokes the frontend build and the Tauri Rust compilation.
```bash
cd frontend
npm run build
cd ../src-tauri
npx @tauri-apps/cli build
```

## 5. macOS Build
The macOS build artifacts are found at:
- `src-tauri/target/release/bundle/macos/cyberscope.app`
- `src-tauri/target/release/bundle/dmg/cyberscope_X.Y.Z_ARCH.dmg`

To test the macOS build in an environment mimicking a fresh machine:
```bash
./src-tauri/target/release/bundle/macos/cyberscope.app/Contents/MacOS/app
```

## 6. Windows Build Strategy
Windows builds are produced through GitHub Actions on a native Windows runner.

Native cross-compilation of PyInstaller and Tauri from macOS to Windows is unreliable, therefore the repository contains a `.github/workflows/windows-build.yml` file.
This workflow natively tests the engine, packages the PyInstaller sidecar (`engine-x86_64-pc-windows-msvc.exe`), builds the React frontend, and uses the `tauri-apps/tauri-action` to construct the final Windows application.

Only after a successful run may the release status become VERIFIED.

## 7. CI Build Instructions
The CI workflow automatically triggers on pushes to the `master` branch.
The output generated `.msi` and `.exe` artifacts are uploaded to the GitHub Actions run via the `upload-artifact` action.

## 8. Offline Requirements
The application requires absolutely NO internet connection.
- All Python dependencies are statically linked in the PyInstaller executable.
- All React components are bundled by Vite.
- All Web Fonts (e.g., Google Fonts) must be either omitted or hosted locally to prevent UI freezing during air-gapped executions.

## 9. Fresh-Machine Testing Procedure
1. Disconnect the machine from Wi-Fi.
2. Transfer the `.dmg` or `.app` via USB.
3. Install and run the application.
4. Verify that the UI loads, the scenarios appear in the dropdown, and "Run Analysis" populates the attack graph and analysis results.

## 10. Known Platform Limitations
- The macOS application must be code-signed (`codesign --force --deep --sign -`) to avoid Gatekeeper warnings on unconfigured machines.
- PyInstaller extracts its runtime to a temporary folder (`/tmp` or `%TEMP%`). Extremely strict endpoint security policies might block execution from the temporary directory.
