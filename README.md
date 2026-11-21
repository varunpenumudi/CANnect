# 🔌 CANnect

CANnect is a modern, lightweight, cross-platform Controller Area Network (CAN) bus analyzer and reverse-engineering tool built with Python, python-can, and NiceGUI.

Inspired by open-source desktop CAN utilities like SavvyCAN, CANgaroo, and BUSMASTER, CANnect provides a dark-themed, responsive web/desktop interface that runs out-of-the-box on any laptop (Windows, Linux, or macOS) without complex C++/Qt build chains.

## ✨ Current Features

- Hardware connection manager supporting Socketcan, GS_USB, Seedstudio interfaces currently

- Live connection status badge and clean connect/disconnect lifecycle management.

- Resizable split-screen layout for Trace tab
  - Top pane displays live unified Rx and Tx traffic
  - Bottom pane provides an inline Transmit Message (Tx) builder.

- Tracks real-time Rx and Tx message counters and relative session timestamps.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+, nicegui 4.0, python_can 4.5

### Installation

1. Clone the repository

```bash
git clone https://github.com/varunpenumudi/CANnect.git
cd CANnect
```

2. Create and activate a virtual environment

```bash
# Create Virtual Environment
python -m venv venv

# Activate - linux / macos
source venv/bin/activate
# Activate - windows
venv\Scripts\activate
```

3. Install required pip packages

```bash
pip install -r requirements.txt
```

4. Run the application entry point

```bash
python main.py
```

NiceGUI will start the local server and open CANnect automatically in your new window.
