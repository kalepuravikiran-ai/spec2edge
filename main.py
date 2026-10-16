import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from openai import OpenAIError

from model import FirmwareScaffold
from tool import analyze_schematic

load_dotenv()

logger = logging.getLogger(__name__)
MAX_IMAGE_SIZE = 10 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_FRAMEWORKS = {
    "Arduino C++",
    "ESP32 MicroPython",
    "Raspberry Pi Pico MicroPython",
    "STM32 C (HAL)",
}

app = FastAPI(
    title="Spec2Edge API",
    description="Multimodal hardware diagram analysis to microcontroller firmware scaffold.",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
async def serve_demo_ui():
    """Serve the browser-based schematic analysis demo."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="theme-color" content="#10151f">
      <title>Spec2Edge — Schematic to firmware</title>
      <style>
        :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #10151f; color: #edf2f7; }
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; background: radial-gradient(ellipse at 50% -20%, #233650 0, #10151f 55%); }
        main { width: min(960px, calc(100% - 32px)); margin: 0 auto; padding: 64px 0; }
        .eyebrow { color: #6ee7b7; font-size: .78rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
        h1 { margin: 12px 0; font-size: clamp(2.2rem, 6vw, 4rem); letter-spacing: -.05em; line-height: 1.05; }
        .intro { max-width: 620px; color: #aab7ca; font-size: 1.08rem; line-height: 1.7; }
        .card, .result-card { margin-top: 32px; padding: 28px; border: 1px solid #2a3546; border-radius: 18px; background: #171e2a; box-shadow: 0 16px 48px #0003; }
        label { display: block; margin: 20px 0 8px; color: #cbd5e1; font-size: .9rem; font-weight: 600; }
        input[type=file], select { width: 100%; padding: 13px; border: 1px solid #354258; border-radius: 10px; background: #111824; color: #edf2f7; }
        input[type=file] { border-style: dashed; }
        .hint { color: #8997aa; font-size: .82rem; }
        button { margin-top: 24px; padding: 13px 20px; border: 0; border-radius: 10px; background: #6ee7b7; color: #10221d; font-size: .95rem; font-weight: 750; cursor: pointer; }
        button:disabled { cursor: wait; opacity: .65; }
        .status { min-height: 24px; margin-top: 16px; color: #fca5a5; }
        [hidden] { display: none !important; }
        .result-heading { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 10px; }
        .result-heading h2 { margin: 0; }
        .badge { padding: 6px 10px; border: 1px solid #345746; border-radius: 999px; color: #6ee7b7; font-size: .82rem; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; margin-top: 12px; border-collapse: collapse; text-align: left; font-size: .9rem; }
        th, td { padding: 11px 12px; border-bottom: 1px solid #2a3546; vertical-align: top; }
        th { color: #aab7ca; font-size: .78rem; letter-spacing: .04em; text-transform: uppercase; }
        pre { overflow-x: auto; padding: 18px; border: 1px solid #2a3546; border-radius: 12px; background: #0b1018; color: #c7f9df; font-size: .84rem; line-height: 1.6; }
        ul { color: #e7c98b; line-height: 1.7; }
        footer { margin-top: 28px; color: #8997aa; font-size: .82rem; }
        @media (max-width: 560px) { main { padding: 40px 0; } .card, .result-card { padding: 20px; } }
      </style>
    </head>
    <body>
      <main>
        <div class="eyebrow">From sketch to scaffold</div>
        <h1>Build from your wiring diagram.</h1>
        <p class="intro">Upload a schematic, breadboard sketch, or pinout drawing. Spec2Edge maps the connections, flags potential wiring hazards, and generates a firmware starting point.</p>
        <section class="card" aria-labelledby="upload-title">
          <h2 id="upload-title">Analyze a diagram</h2>
          <form id="uploadForm">
            <label for="imageFile">Diagram image</label>
            <input type="file" id="imageFile" accept="image/jpeg,image/png,image/webp" required>
            <p class="hint">JPG, PNG, or WEBP · up to 10 MB</p>
            <label for="framework">Target framework</label>
            <select id="framework">
              <option value="Arduino C++">Arduino C++</option>
              <option value="ESP32 MicroPython">ESP32 MicroPython</option>
              <option value="Raspberry Pi Pico MicroPython">Raspberry Pi Pico MicroPython</option>
              <option value="STM32 C (HAL)">STM32 C (HAL)</option>
            </select>
            <button type="submit" id="submitBtn">Analyze diagram</button>
            <div id="status" class="status" role="status" aria-live="polite"></div>
          </form>
        </section>
        <section id="outputArea" class="result-card" aria-live="polite" hidden>
          <div class="result-heading">
            <h2 id="mcuDetected"></h2>
            <span id="frameworkBadge" class="badge"></span>
          </div>
          <h3>Pin connections</h3>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Component</th><th>Component pin</th><th>MCU pin</th><th>Protocol</th><th>Notes</th></tr></thead>
              <tbody id="pinTable"></tbody>
            </table>
          </div>
          <h3>Required libraries</h3>
          <ul id="libraries"></ul>
          <h3>Wiring audit</h3>
          <ul id="auditNotes"></ul>
          <h3>Generated firmware</h3>
          <pre><code id="codeBlock"></code></pre>
        </section>
        <footer>AI-generated wiring and firmware suggestions can be incorrect. Verify every connection and review the code before powering hardware.</footer>
      </main>
      <script>
        const form = document.getElementById("uploadForm");
        const status = document.getElementById("status");
        const output = document.getElementById("outputArea");
        const addListItems = (list, values) => {
          list.replaceChildren();
          for (const value of values) {
            const item = document.createElement("li");
            item.textContent = value;
            list.appendChild(item);
          }
        };

        form.addEventListener("submit", async (event) => {
          event.preventDefault();
          const button = document.getElementById("submitBtn");
          const image = document.getElementById("imageFile").files[0];
          status.textContent = "";
          output.hidden = true;
          button.disabled = true;
          button.textContent = "Analyzing…";

          const formData = new FormData();
          formData.append("file", image);
          formData.append("framework", document.getElementById("framework").value);

          try {
            const response = await fetch("/api/v1/analyze", { method: "POST", body: formData });
            if (!response.ok) {
              const error = await response.json().catch(() => ({}));
              throw new Error(error.detail || "Analysis failed. Please try again.");
            }
            const data = await response.json();
            document.getElementById("mcuDetected").textContent = data.target_mcu;
            document.getElementById("frameworkBadge").textContent = data.framework;
            const table = document.getElementById("pinTable");
            table.replaceChildren();
            for (const pin of data.pin_connections) {
              const row = document.createElement("tr");
              for (const value of [pin.component_name, pin.component_pin, pin.mcu_pin, pin.protocol, pin.notes || "—"]) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
              }
              table.appendChild(row);
            }
            addListItems(document.getElementById("libraries"), data.required_libraries);
            addListItems(document.getElementById("auditNotes"), data.wiring_audit_notes);
            document.getElementById("codeBlock").textContent = data.source_code;
            output.hidden = false;
          } catch (error) {
            status.textContent = error.message;
          } finally {
            button.disabled = false;
            button.textContent = "Analyze diagram";
          }
        });
      </script>
    </body>
    </html>
    """


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=FirmwareScaffold)
async def analyze_diagram_endpoint(
    file: UploadFile = File(...),
    framework: str = Form("Arduino C++"),
):
    """Analyze an uploaded diagram and return a validated firmware scaffold."""
    if file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WEBP image.",
        )

    if framework not in SUPPORTED_FRAMEWORKS:
        raise HTTPException(status_code=400, detail="Unsupported target framework.")

    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")

    try:
        scaffold = analyze_schematic(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            preferred_framework=framework,
        )
    except ValueError as error:
        logger.error("Schematic analysis is not configured: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Schematic analysis is not configured. Set OPENAI_API_KEY.",
        ) from error
    except OpenAIError as error:
        logger.exception("OpenAI schematic analysis failed")
        raise HTTPException(
            status_code=502,
            detail="The analysis provider could not process this diagram. Please try again.",
        ) from error

    return scaffold


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
