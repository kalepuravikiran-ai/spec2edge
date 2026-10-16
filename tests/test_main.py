import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import MAX_IMAGE_SIZE, app
from model import FirmwareScaffold


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_homepage_and_health_check(self):
        homepage = self.client.get("/")
        self.assertEqual(homepage.status_code, 200)
        self.assertIn("Spec2Edge", homepage.text)
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})

    def test_reports_analysis_availability_without_exposing_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-secret"}):
            response = self.client.get("/api/v1/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"analysis_available": True})
        self.assertNotIn("test-secret", response.text)

    def test_reports_missing_analysis_configuration(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            response = self.client.get("/api/v1/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"analysis_available": False})

    def test_rejects_unsupported_image_type(self):
        response = self.client.post(
            "/api/v1/analyze",
            files={"file": ("diagram.gif", b"image", "image/gif")},
        )
        self.assertEqual(response.status_code, 400)

    def test_rejects_image_with_invalid_contents(self):
        with patch("main.analyze_schematic") as analyze_schematic:
            response = self.client.post(
                "/api/v1/analyze",
                files={"file": ("diagram.png", b"not actually an image", "image/png")},
            )
        self.assertEqual(response.status_code, 400)
        analyze_schematic.assert_not_called()

    def test_rejects_unsupported_framework(self):
        response = self.client.post(
            "/api/v1/analyze",
            files={"file": ("diagram.png", b"image", "image/png")},
            data={"framework": "Unsupported"},
        )
        self.assertEqual(response.status_code, 400)

    def test_rejects_oversized_image(self):
        response = self.client.post(
            "/api/v1/analyze",
            files={"file": ("diagram.png", b"x" * (MAX_IMAGE_SIZE + 1), "image/png")},
        )
        self.assertEqual(response.status_code, 413)

    @patch("main.analyze_schematic")
    def test_returns_firmware_scaffold(self, analyze_schematic):
        analyze_schematic.return_value = FirmwareScaffold(
            target_mcu="ESP32",
            framework="Arduino C++",
            required_libraries=[],
            pin_connections=[],
            source_code="void setup() {}",
            wiring_audit_notes=[],
        )

        response = self.client.post(
            "/api/v1/analyze",
            files={
                "file": (
                    "diagram.png",
                    b"\x89PNG\r\n\x1a\nimage",
                    "image/png",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["target_mcu"], "ESP32")
        analyze_schematic.assert_called_once_with(
            image_bytes=b"\x89PNG\r\n\x1a\nimage",
            mime_type="image/png",
            preferred_framework="Arduino C++",
        )

    @patch("main.analyze_schematic", side_effect=ValueError("missing key"))
    def test_reports_missing_api_key_clearly(self, _analyze_schematic):
        response = self.client.post(
            "/api/v1/analyze",
            files={
                "file": (
                    "diagram.png",
                    b"\x89PNG\r\n\x1a\nimage",
                    "image/png",
                )
            },
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
