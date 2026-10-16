import base64
import os
from openai import OpenAI
from model import FirmwareScaffold

SYSTEM_PROMPT = """You are an expert embedded systems engineer, electrical schematic auditor, and firmware architect.
Your job is to analyze hand-drawn hardware block diagrams, breadboard sketches, or circuit schematics.

Extract every component, detect the intended microcontroller, trace pin interconnects, check for electrical conflicts (e.g., 5V logic feeding directly into 3.3V GPIOs, missing I2C pull-ups, wrong bus pins), and write industrial-grade initialization and driver loop code.

Always format the output strictly adhering to the FirmwareScaffold schema."""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing.")
    return OpenAI(api_key=api_key)


def encode_image(image_bytes: bytes) -> str:
    """Converts raw image bytes to a base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_schematic(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    preferred_framework: str = "Arduino C++"
) -> FirmwareScaffold:
    """
    Submits a hardware diagram image to OpenAI Vision with strict schema validation.
    """
    client = get_openai_client()
    base64_img = encode_image(image_bytes)

    user_prompt = f"""Analyze this hand-drawn block diagram / hardware sketch.
1. Identify all microcontrollers, sensors, actuators, and displays.
2. Trace the interconnects and map out the pinout table.
3. Write production-ready scaffold firmware using: {preferred_framework}.
4. Provide hardware audit warnings for any electrical or protocol issues."""

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_img}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        response_format=FirmwareScaffold,
        temperature=0.2
    )

    return response.choices[0].message.parsed