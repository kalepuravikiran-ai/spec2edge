# Spec2Edge: Multimodal Diagram to Embedded Firmware Scaffold

## Overview
Spec2Edge is an open-source development bridge that converts physical whiteboard schematics, notebook pin diagrams, and sensor block diagrams into verified microcontroller firmware scaffolds, hardware audit reports, and pin-assignment manifests.

### Why It Scales For Everyone
- **For Makers & Students:** Eliminates syntax confusion and wiring pinout lookups by generating immediate setup loops.
- **For Professional Embedded Engineers:** Automates board bring-up boilerplate, creates initial pin-mux tables, and audits hardware designs for mismatched logic voltages (e.g., 5V sensors tied to 3.3V ADC inputs).
- **For Open-Source Maintainers:** Acts as a continuous documentation tool that generates board support packages (BSPs) directly from schematic figures.

---

## Technical Architecture
1. **Input Layer:** Multi-format image capture (JPEG/PNG/WEBP).
2. **Analysis Pipeline:** GPT-4o multimodal vision parsing constrained with strict Pydantic JSON schema invariants (`FirmwareScaffold`).
3. **Firmware Engine:** Generates idiomatic code supporting multiple frameworks (Arduino C++, ESP32 MicroPython, Pico SDK, and STM32 HAL).
4. **Safety & Audit Pass:** Flags common physical wiring pitfalls (floating reset pins, missing pull-ups, logic level mismatch).

---

## Quickstart Guide

### 1. Environment Setup
```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt