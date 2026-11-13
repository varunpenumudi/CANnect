from typing import Any, Callable, Dict
from nicegui import ui
from core.can_backend import CANBackend

PANEL_DARK = "#1A222D"
BORDER_DARK = "#283548"
SUBPANEL_DARK = "#141B24"


def build_connection_dialog(
    backend: CANBackend, on_status_change: Callable[[bool, str], None]
) -> ui.dialog:
    # Holds references to whichever widgets are currently rendered for the active bus type
    controls: Dict[str, Any] = {}

    with ui.dialog() as dialog, ui.card().style(
        f"background: {PANEL_DARK}; border: 1px solid {BORDER_DARK}; min-width: 480px; padding: 24px; border-radius: 8px;"
    ):
        ui.label("CAN Bus Connection Settings").classes("text-lg font-bold text-white mb-1")
        ui.label(
            "Select bus hardware type to load its configuration options:"
        ).classes("text-xs text-gray-400 mb-4")

        # 1. Select Bus Type
        bus_type_select = (
            ui.select(
                options={
                    "canable": "CANable (candleLight GS-USB)",
                    "seeedstudio": "SeeedStudio USB-CAN Analyzer",
                    "socketcan": "SocketCAN (Linux Native / vcan)",
                },
                label="Bus Driver Type",
            )
            .props("dark outlined dense options-dark")
            .classes("w-full mb-3")
        )

        # 2. Dynamic Container where driver-specific elements are created on selection
        options_container = ui.column().classes("w-full gap-3 mb-4")

        def on_bus_change():
            b_type = bus_type_select.value
            options_container.clear()
            controls.clear()

            if not b_type:
                return

            detected_ports = backend.detect_interfaces(b_type)

            with options_container:
                with ui.column().style(
                    f"background: {SUBPANEL_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 6px;"
                ).classes("w-full p-3 gap-3"):

                    # Common Interface / Port Selector + Rescan
                    with ui.row().classes("w-full items-center gap-2"):
                        controls["channel"] = (
                            ui.select(
                                options=detected_ports,
                                value=detected_ports[0] if detected_ports else None,
                                label="Available Interface / Port",
                                with_input=True,
                            )
                            .props("dark outlined dense options-dark")
                            .classes("flex-grow")
                        )

                        def rescan():
                            ports = backend.detect_interfaces(b_type)
                            controls["channel"].options = ports
                            controls["channel"].value = ports[0] if ports else None
                            controls["channel"].update()

                        ui.button(icon="refresh", on_click=rescan).props(
                            "flat dense round color=blue-4"
                        ).tooltip("Rescan Interfaces")

                    # Common Nominal Bitrate
                    controls["bitrate"] = (
                        ui.select(
                            options={
                                125000: "125 kbit/s",
                                250000: "250 kbit/s",
                                500000: "500 kbit/s (Standard)",
                                1000000: "1000 kbit/s (1 Mbps)",
                            },
                            value=500000,
                            label="Nominal Bitrate",
                        )
                        .props("dark outlined dense options-dark")
                        .classes("w-full")
                    )

                    # ---------------- DRIVER-SPECIFIC ELEMENTS ----------------
                    if b_type == "socketcan":
                        with ui.row().classes("w-full justify-between items-center"):
                            controls["fd"] = ui.checkbox("Enable CAN-FD").props("dark dense")
                            controls["loopback"] = ui.checkbox("Loopback Mode").props("dark dense")

                        controls["data_bitrate"] = (
                            ui.select(
                                options={
                                    1000000: "1 Mbit/s",
                                    2000000: "2 Mbit/s (Standard FD)",
                                    4000000: "4 Mbit/s",
                                    5000000: "5 Mbit/s",
                                },
                                value=2000000,
                                label="CAN-FD Data Bitrate",
                            )
                            .props("dark outlined dense options-dark")
                            .classes("w-full")
                        )
                        controls["data_bitrate"].bind_visibility_from(controls["fd"], "value")

                    elif b_type == "canable":
                        ui.label(
                            "candleLight GS-USB uses native libusb/WinUSB (Channel 0 = first adapter)."
                        ).classes("text-xs text-gray-400")
                    
                    elif b_type == "seeedstudio":
                        controls["tty_baud"] = (
                            ui.select(
                                options={
                                    9600: "9600 bps",
                                    115200: "115200 bps",
                                    2000000: "2000000 bps (Default)",
                                },
                                value=2000000,
                                label="Serial Baudrate",
                            )
                            .props("dark outlined dense options-dark")
                            .classes("w-full")
                        )
                        with ui.row().classes("w-full gap-2"):
                            controls["op_mode"] = (
                                ui.select(
                                    options=["normal", "loopback", "silent", "loopback_and_silent"],
                                    value="normal",
                                    label="Operation Mode",
                                )
                                .props("dark outlined dense options-dark")
                                .classes("flex-grow")
                            )
                            controls["frame_type"] = (
                                ui.select(
                                    options={"STD": "Standard (11-bit)", "EXT": "Extended (29-bit)"},
                                    value="STD",
                                    label="Frame Type",
                                )
                                .props("dark outlined dense options-dark")
                                .classes("w-44")
                            )

        bus_type_select.on("update:model-value", on_bus_change)

        # 3. Apply Connection using active controls
        def apply_connection():
            b_type = bus_type_select.value
            if not b_type or "channel" not in controls:
                ui.notify("Please select a Bus Driver Type first", color="warning")
                return

            channel = controls["channel"].value
            bitrate = controls["bitrate"].value

            if b_type == "socketcan":
                kwargs = {
                    "fd": controls["fd"].value,
                    "receive_own_messages": controls["loopback"].value,
                }
                if controls["fd"].value:
                    kwargs["data_bitrate"] = controls["data_bitrate"].value
                ok = backend.connect(bustype="socketcan", channel=channel, bitrate=bitrate, **kwargs)

            elif b_type == "canable":
                gs_channel = int(channel) if str(channel).isdigit() else 0
                ok = backend.connect(
                    bustype="gs_usb",
                    channel=gs_channel,
                    bitrate=bitrate,
                )
                channel = f"gs_usb:{gs_channel}"
            
            elif b_type == "seeedstudio":
                ok = backend.connect(
                    bustype="seeedstudio",
                    channel=channel,
                    bitrate=bitrate,
                    baudrate=controls["tty_baud"].value,
                    operation_mode=controls["op_mode"].value,
                    frame_type=controls["frame_type"].value,
                )
            
            else:
                ok = False

            if ok:
                ui.notify(f"Connected to {channel} @ {bitrate} bps", color="positive")
            else:
                ui.notify(f"Failed to connect to {channel}", color="negative")

            on_status_change(ok, str(channel))
            dialog.close()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=grey")
            ui.button("Connect Bus", on_click=apply_connection).props("color=primary")

    return dialog