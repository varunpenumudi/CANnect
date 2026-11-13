import glob
import os
import time
from serial.tools.list_ports import comports as list_comports
from typing import Dict, List, Optional
import can
import sys

class CANBackend:
    def __init__(self):
        self.bus: Optional[can.BusABC] = None
        self.is_connected: bool = False
        self.is_running: bool = False
        self.rx_messages: List[Dict] = []
        self.tx_messages: List[Dict] = []
        self.rx_count: int = 0
        self.tx_count: int = 0
        self.error_count: int = 0
        self.current_channel: Optional[str | int] = None
        self.current_bustype: str = "socketcan"

    def detect_interfaces(self, bustype: str) -> List[str]:
        interfaces = []
        try:
            if bustype == "socketcan":
                configs = can.detect_available_configs(interfaces=["socketcan"])
                interfaces = [str(cfg["channel"]) for cfg in configs if "channel" in cfg]
            elif bustype == "seeedstudio":
                interfaces = [p.device for p in list_comports()]
            elif bustype == "canable":
                configs = can.detect_available_configs(interfaces=["gs_usb"])
                interfaces = [str(cfg["channel"]) for cfg in configs if "channel" in cfg]
        except Exception as e:
            print(f"[CAN Warning] Interface scan failed for {bustype}: {e}")

        return interfaces

    def connect(self, bustype: str, channel: Optional[str | int], bitrate: int, **kwargs) -> bool:
        self.disconnect()
        self.current_bustype = bustype
        self.current_channel = channel
        try:
            self.bus = can.Bus(
                interface=bustype, channel=channel, bitrate=bitrate, **kwargs
            )
            self.is_connected = True
            self.is_running = True
            return True
        except Exception as e:
            print(f"[CAN Error] Connection failed: {e}")
            self.is_connected = False
            self.is_running = False
            return False

    def disconnect(self):
        self.is_running = False
        self.is_connected = False
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None

    def send_message(
        self, arbitration_id: int, data: bytes, is_extended_id: bool = False
    ) -> bool:
        if not self.is_connected or not self.bus:
            return False
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
            check=True,
        )
        try:
            self.bus.send(msg)
            self.tx_count += 1
            self.tx_messages.insert(
                0,
                {
                    "timestamp": f"{time.time() % 1000:.3f}",
                    "channel": self.current_channel,
                    "type": "Tx",
                    "id": (
                        f"0x{arbitration_id:03X}"
                        if not is_extended_id
                        else f"0x{arbitration_id:08X}"
                    ),
                    "dlc": len(data),
                    "data": " ".join(f"{b:02X}" for b in data),
                },
            )
            if len(self.tx_messages) > 1000:
                self.tx_messages.pop()
            return True
        except Exception as e:
            print(f"[CAN Tx Error] {e}")
            self.error_count += 1
            return False

    def poll_rx(self) -> Optional[Dict]:
        if not self.is_connected or not self.is_running or not self.bus:
            return None
        try:
            msg = self.bus.recv(timeout=0.0)
            if msg:
                self.rx_count += 1
                row = {
                    "timestamp": f"{msg.timestamp % 1000:.4f}",
                    "channel": self.current_channel,
                    "type": "Rx",
                    "id": (
                        f"0x{msg.arbitration_id:03X}"
                        if not msg.is_extended_id
                        else f"0x{msg.arbitration_id:08X}"
                    ),
                    "dlc": msg.dlc,
                    "data": " ".join(f"{b:02X}" for b in msg.data),
                }
                self.rx_messages.insert(0, row)
                if len(self.rx_messages) > 1000:
                    self.rx_messages.pop()
                return row
        except Exception:
            self.error_count += 1
        return None