from typing import List, Optional
from pydantic import BaseModel, Field


class PinConnection(BaseModel):
    component_name: str = Field(description="Name of the sensor, display, or peripheral (e.g., DHT22, SSD1306)")
    component_pin: str = Field(description="Pin on the peripheral (e.g., VCC, GND, SDA, DATA)")
    mcu_pin: str = Field(description="Target pin on the microcontroller (e.g., GPIO 21, A0, 3V3, GND)")
    protocol: str = Field(description="Protocol or interface type: GPIO, I2C, SPI, UART, ADC, or PWM")
    notes: Optional[str] = Field(default="", description="Pull-up resistor requirements, voltage tolerances, etc.")


class FirmwareScaffold(BaseModel):
    target_mcu: str = Field(description="Identified microcontroller (e.g., ESP32, Arduino Uno, Raspberry Pi Pico)")
    framework: str = Field(description="Target framework (e.g., Arduino C++, MicroPython, CircuitPython)")
    required_libraries: List[str] = Field(description="Third-party libraries required (e.g., Adafruit_SSD1306, DHT sensor library)")
    pin_connections: List[PinConnection] = Field(description="Table of all mapped electrical connections")
    source_code: str = Field(description="Complete, compilation-ready boilerplate code with pin defines and read loops")
    wiring_audit_notes: List[str] = Field(description="Potential electrical hazards, pin clashes, or voltage level warnings")