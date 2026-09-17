# CyberScope Phase 3C — LLM Benchmark Contexts

## Purpose
This directory contains sanitized `InvestigationLLMContext` JSON files
for external LLM benchmarking (e.g., Google Colab).

## Security
- **NO ground truth** is present in any context file.
- All evidence references are real pipeline identifiers.
- Forbidden fields are recursively scanned and rejected at export time.

## Contents
- `contexts/` — 30 JSON context files
- `manifest.json` — Benchmark metadata (NO hidden answers)
- `evaluator_metadata.json` — Expected classifications for scoring (NEVER pass to LLM)
- `README.md` — This file

## Distribution
- OBSERVED: 10
- INFERRED: 10
- UNKNOWN: 10

## Reproduction
Seed: 42
Run: `cd engine && python -m llm.benchmark_export`
