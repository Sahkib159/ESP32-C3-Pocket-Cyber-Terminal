# ESP32-C3 Pocket Cyber Terminal

A cyberpunk-style desktop terminal built with Python and an ESP32-C3 Super Mini. The application communicates with the board over USB serial and provides a terminal interface for inspecting basic device information and scanning nearby Wi-Fi networks.

## Features

- Cyberpunk-inspired desktop interface
- USB serial communication with ESP32-C3
- Device status and uptime commands
- Basic memory and chip information
- Nearby Wi-Fi network scanning
- Quick-command buttons and interactive terminal input

## Hardware

- ESP32-C3 Super Mini
- USB data cable
- Windows PC

## Software

- Arduino IDE
- Python 3
- `pyserial`
- Tkinter

## Setup

1. Install the Arduino IDE and the ESP32 board support package.
2. Upload the ESP32 firmware from the Arduino sketch included in this repository.
3. Install Python 3 on your computer.
4. Install the serial communication library:

   ```bash
   python -m pip install pyserial
   ```

5. Close the Arduino IDE Serial Monitor so it releases the board's COM port.
6. Run the desktop application:

   ```bash
   python cyber_terminal.py
   ```

7. Select the ESP32-C3's COM port, connect, and try the available commands.

## Commands

| Command | Purpose |
|---|---|
| `help` | List available commands |
| `status` | Display device status |
| `uptime` | Show device uptime |
| `memory` | Display basic memory information |
| `chip` | Display chip information |
| `scan` | Scan for nearby Wi-Fi networks |

## Project Goals

This project explores embedded systems, serial communication, Python desktop applications, and basic wireless network discovery.

## Disclaimer

Use network-scanning functionality responsibly and only in environments where you are authorized to operate.

## Author

Built as a personal CSE and embedded-systems learning project.
