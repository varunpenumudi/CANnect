from typing import Callable
from nicegui import ui
from core.can_backend import CANBackend

PANEL_DARK = "#1A222D"
BORDER_DARK = "#283548"


def build_connection_dialog(
    backend: CANBackend, on_status_change: Callable[[bool, str], None]
) -> ui.dialog:
    with ui.dialog() as dialog, ui.card().style(
        f"background: {PANEL_DARK}; border: 1px solid {BORDER_DARK}; min-width: 480px; padding: 24px; border-radius: 8px;"
    ):
        ui.label("CAN Bus Connection Settings").classes("text-lg font-bold text-white mb-2")
        ui.label(
            "Select bus hardware type and configure communication parameters:"
        ).classes("text-xs text-gray-400 mb-4")

        bus_type_select = ui.select(
            options=["socketcan", "seeedstudio"],
            value="socketcan",
            label="Bus Driver Type",
        ).classes("w-full mb-3")

        initial_ifaces = backend.detect_interfaces("socketcan")
        channel_select = ui.select(
            options=initial_ifaces,
            value=initial_ifaces[0] if initial_ifaces else "",
            label="Available CAN Bus Interface",
        ).classes("w-full mb-3")

        bitrate_select = ui.select(
            options={
                125000: "125 kbit/s",
                250000: "250 kbit/s",
                500000: "500 kbit/s (Standard)",
                1000000: "1000 kbit/s (1 Mbps)",
            },
            value=500000,
            label="Nominal Bitrate",
        ).classes("w-full mb-3")

        with ui.row().classes("w-full justify-between items-center mb-4"):
            fd_toggle = ui.checkbox("Enable CAN-FD").props("dense")
            loopback_toggle = ui.checkbox("Loopback Mode").props("dense")

        def on_bus_type_change():
            detected = backend.detect_interfaces(bus_type_select.value)
            channel_select.options = detected
            channel_select.value = detected[0] if detected else ""
            channel_select.update()

        bus_type_select.on("update:model-value", on_bus_type_change)

        def apply_connection():
            ok = backend.connect(
                bustype=bus_type_select.value,
                channel=channel_select.value,
                bitrate=bitrate_select.value,
                fd=fd_toggle.value,
                receive_own_messages=loopback_toggle.value,
            )
            if ok:
                ui.notify(
                    f"Connected to {channel_select.value} @ {bitrate_select.value} bps",
                    color="positive",
                )
            else:
                ui.notify(
                    f"Failed to connect to {channel_select.value}", color="negative"
                )
            on_status_change(ok, channel_select.value)
            dialog.close()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=grey")
            ui.button("Connect Bus", on_click=apply_connection).props("color=primary")

    return dialog