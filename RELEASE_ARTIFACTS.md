# Release Artifacts

The following desktop application artifacts have been compiled and evaluated.

## macOS (Apple Silicon)
- **Path:** `src-tauri/target/release/bundle/macos/cyberscope.app`
- **DMG Path:** `src-tauri/target/release/bundle/dmg/cyberscope_0.1.0_aarch64.dmg`
- **App Architecture:** `aarch64-apple-darwin`
- **Sidecar Architecture:** `engine-aarch64-apple-darwin`
- **Build Command:** `npm run tauri build` (wrapping `cargo tauri build`)
- **Status:** VERIFIED

## Windows
- **Path:** N/A
- **App Architecture:** `x86_64-pc-windows-msvc`
- **Status:** UNVERIFIED
- **Note:** A Windows `.exe`/`.msi` is not currently bundled in this repository to prevent delivering a corrupted cross-compiled binary. As documented in `PACKAGING.md`, the Windows artifact must be generated on a native Windows CI runner (e.g., GitHub Actions `windows-latest`). The CI workflow instructions are fully provided, but the execution remains UNVERIFIED in the local macOS environment.
