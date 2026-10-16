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

    def test_rejects_unsupported_image_type(self):
        response = self.client.post(
            "/api/v1/analyze",
            files={"file": ("diagram.gif", b"image", "image/gif")},
        )
        self.assertEqual(response.status_code, 400)

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
            files={"file": ("diagram.png", b"image", "image/png")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["target_mcu"], "ESP32")
        analyze_schematic.assert_called_once_with(
            image_bytes=b"image",
            mime_type="image/png",
            preferred_framework="Arduino C++",
        )


if __name__ == "__main__":
    unittest.main()
