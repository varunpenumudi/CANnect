import os
import sys
import time
from typing import Dict, List, Optional
import can
from serial.tools.list_ports import comports as list_comports


class CANBackend:
    def __init__(self):
        self.bus: Optional[can.BusABC] = None
        self.is_connected: bool = False
        self.is_running: bool = False
        self.messages: List[Dict] = []  # Unified Rx + Tx trace buffer
        self.rx_count: int = 0
        self.tx_count: int = 0
        self.error_count: int = 0
        self.msg_uid: int = 0
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

    def _append_trace_row(self, msg_type: str, arb_id: int, is_ext: bool, dlc: int, data: bytes | bytearray, timestamp: float) -> Dict:
        self.msg_uid += 1
        row = {
            "uid": self.msg_uid,
            "timestamp": f"{timestamp % 1000:.4f}",
            "channel": self.current_channel,
            "type": msg_type,
            "id": f"0x{arb_id:03X}" if not is_ext else f"0x{arb_id:08X}",
            "dlc": dlc,
            "data": " ".join(f"{b:02X}" for b in data),
        }
        self.messages.insert(0, row)
        if len(self.messages) > 1000:
            self.messages.pop()
        return row

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
            self._append_trace_row(
                msg_type="Tx",
                arb_id=arbitration_id,
                is_ext=is_extended_id,
                dlc=len(data),
                data=data,
                timestamp=time.time(),
            )
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
                return self._append_trace_row(
                    msg_type="Rx",
                    arb_id=msg.arbitration_id,
                    is_ext=msg.is_extended_id,
                    dlc=msg.dlc,
                    data=msg.data,
                    timestamp=msg.timestamp or time.time(),
                )
        except Exception:
            self.error_count += 1
        return None