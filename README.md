# Spec2Edge

Spec2Edge analyzes a photo of a hardware schematic or wiring sketch, maps component-to-microcontroller connections, highlights potential wiring hazards, and generates a firmware scaffold for the selected framework.

## Run locally

Requirements: Python 3.10 or newer and an OpenAI API key.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your key to `.env`:

```text
OPENAI_API_KEY=your-key
```

Start the application:

```powershell
python -m uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000). The health endpoint is [http://localhost:8000/healthz](http://localhost:8000/healthz), and the interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

The browser demo accepts JPG, PNG, and WEBP images up to 10 MB and checks that each file's contents match its image type before analysis. The `/api/v1/status` endpoint reports whether analysis is configured without revealing the key. Analysis uses the OpenAI API and incurs usage charges on the account whose API key is configured. Treat the generated firmware and wiring audit as suggestions; verify them against the actual board and component datasheets before connecting or powering hardware.

## Deploy publicly with Render

1. Push this project to a GitHub repository. Keep `.env` out of the repository; `.gitignore` excludes it.
2. In Render, create a new **Blueprint** and connect that repository. Render reads `render.yaml` to build and start the web service.
3. The Blueprint requests Render's free web-service plan and does not require an API key to create the public site. To enable diagram analysis, add `OPENAI_API_KEY` under the service's **Environment** settings in Render and select **Save, rebuild, and deploy**. Confirm the key is saved as a non-empty value without exposing it in chat, source control, or logs. Do not put the key in `render.yaml` or GitHub.
4. Wait for the deployment and health check to pass; Render provides a public `https://<service-name>.onrender.com` URL. Free services can spin down after inactivity and take a little time to start again.

The service uses the configured API key for every visitor's analysis. Share the URL only with that in mind, and set usage limits or billing alerts on the OpenAI account.

## API

`POST /api/v1/analyze` accepts multipart form fields `file` (an image) and `framework` (optional; defaults to `Arduino C++`). The response matches the `FirmwareScaffold` schema in `model.py`.
