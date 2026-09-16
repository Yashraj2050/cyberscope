# CyberScope Demo Guide

This guide outlines an exact 60–90 second workflow for presenting CyberScope to the SIH judges.

## Prerequisites
- The machine must be strictly air-gapped (no Wi-Fi, no internet).
- The `cyberscope.app` desktop application must be pre-launched or visible on the dock.

## Presenter Script & Action Flow

**00:00 Launch CyberScope**
*(Action: Click the CyberScope icon to open the application.)*
"Welcome to CyberScope. CyberScope is an offline, evidence-aware investigation system designed to reconstruct missing transitions in incomplete attack telemetry."

**00:05 Select scenario**
*(Action: Open the Scenario Selection dropdown in the sidebar and choose "Scenario 001: Ambiguous Reconstruction".)*
"Here we load a fragment of raw, incomplete telemetry."

**00:10 Run analysis**
*(Action: Click the 'Run Analysis' button.)*
"As the analysis runs, CyberScope mathematically evaluates the observed events..."

**00:20 Show telemetry**
*(Action: Briefly gesture to the raw telemetry table.)*
"...and parses them into a chronological event ledger."

**00:30 Show attack graph**
*(Action: Gesture to the central interactive attack graph. Zoom or pan slightly if needed.)*
"It then stitches this telemetry into a directed graph, tracking the timeline across hosts, users, and processes."

**00:40 Show detected gap**
*(Action: Point to the highlighted Gap Node on the graph.)*
"Here, the Gap Detector identified a structural break in continuity. The telemetry jumped without a logical precursor."

**00:50 Show candidate hypotheses**
*(Action: Click the Gap Node to open the Investigation Inspector on the right. Expand the Candidates section.)*
"CyberScope instantly proposes the most plausible MITRE ATT&CK techniques that fit this gap. It calculates a strict candidate score for each, representing the level of evidence support."

**01:00 Show evidence verification**
*(Action: Scroll down to the Evidence Verification section.)*
"It then rigorously verifies the top candidates against six distinct dimensions: temporal feasibility, host, user, and process constraints, ensuring the hypothesis doesn't violently contradict known facts."

**01:10 Show final classification**
*(Action: Highlight the final status badge at the top of the Inspector.)*
"Crucially, CyberScope does not fill the gap by pretending the missing event is known. It evaluates the surrounding evidence, generates candidate transitions, verifies them, and returns UNKNOWN when the evidence cannot distinguish between plausible candidates—just as it did here due to an exact score tie. It refuses to hallucinate."

**01:20 Show export**
*(Action: Click the 'Export JSON' button.)*
"Finally, we can securely export the verified reconstruction pipeline artifacts for downstream reporting."
