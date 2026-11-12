from nicegui import ui
from core.can_backend import CANBackend

BG_DARK = "#121820"
PANEL_DARK = "#1A222D"
BORDER_DARK = "#283548"

TRACE_COLUMNS = [
    {"name": "timestamp", "label": "Time (s)", "field": "timestamp", "align": "left", "sortable": True},
    {"name": "channel", "label": "Ch", "field": "channel", "align": "center"},
    {"name": "type", "label": "Type", "field": "type", "align": "center"},
    {"name": "id", "label": "CAN ID", "field": "id", "align": "left", "sortable": True},
    {"name": "dlc", "label": "DLC", "field": "dlc", "align": "center"},
    {"name": "data", "label": "Data (Hex Payload)", "field": "data", "align": "left"},
]


class TraceTab:
    def __init__(self, backend: CANBackend):
        self.backend = backend
        self.is_horizontal = True  # True = Top/Bottom split, False = Left/Right split
        self.container = ui.column().classes("w-full h-full gap-1")

        with self.container:
            # Compact Trace Toolbar for Split Orientation & Quick Reset
            with ui.row().style(
                f"background: {PANEL_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 4px;"
            ).classes("w-full items-center justify-between px-3 py-1"):
                ui.label("CAN Trace & Transmit Workspace").classes("text-xs font-bold text-gray-300")
                with ui.row().classes("items-center gap-2"):
                    self.split_btn = ui.button(
                        "Split: Top / Bottom",
                        icon="vertical_split",
                        on_click=self.toggle_split_orientation,
                    ).props("flat dense no-caps size=sm color=blue-4")

            # Resizable Split Pane (Both Rx and Tx visible simultaneously)
            self.splitter = ui.splitter(horizontal=True, value=60).classes(
                "w-full flex-grow"
            ).style(f"background: {BG_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 4px;")

            # ---------------- TOP / LEFT PANE: INCOMING MESSAGES (RX) ----------------
            with self.splitter.before:
                with ui.column().classes("w-full h-full p-2 gap-1"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label("INCOMING MESSAGES (RX)").classes("text-xs font-bold text-emerald-400")
                        self.rx_counter_lbl = ui.label("0 frames").classes("text-xs text-gray-400")

                    self.rx_table = (
                        ui.table(
                            columns=TRACE_COLUMNS,
                            rows=[],
                            row_key="timestamp",
                            pagination={"rowsPerPage": 25},
                        )
                        .classes("w-full flex-grow")
                        .props("dense flat bordered dark virtual-scroll")
                    )

            # ---------------- BOTTOM / RIGHT PANE: TRANSMIT MESSAGES (TX) ----------------
            with self.splitter.after:
                with ui.column().classes("w-full h-full p-2 gap-2"):
                    ui.label("TRANSMITTED MESSAGES (TX)").classes("text-xs font-bold text-blue-400")

                    # Transmitted History Table
                    self.tx_table = (
                        ui.table(
                            columns=TRACE_COLUMNS,
                            rows=[],
                            row_key="timestamp",
                            pagination={"rowsPerPage": 10},
                        )
                        .classes("w-full flex-grow")
                        .props("dense flat bordered dark virtual-scroll")
                    )

                    # Sender Control Bar
                    with ui.row().style(
                        f"background: {PANEL_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 4px;"
                    ).classes("w-full items-center gap-3 p-2"):
                        tx_id = ui.input(label="CAN ID (Hex)", value="1A0").props("dark outlined dense").classes("w-32")
                        tx_dlc = ui.number(label="DLC", value=8, min=0, max=8).props("dark outlined dense").classes("w-20")
                        tx_data = ui.input(
                            label="Data Bytes (Hex)", value="11 22 33 44 55 66 77 88"
                        ).props("dark outlined dense").classes("flex-grow")
                        tx_ext = ui.checkbox("Ext ID").props("dark dense")

                        def handle_send():
                            try:
                                arb_id = int(tx_id.value, 16)
                                clean_hex = tx_data.value.replace(" ", "")
                                payload = bytes.fromhex(clean_hex)[: int(tx_dlc.value)]
                                if self.backend.send_message(
                                    arb_id, payload, is_extended_id=tx_ext.value
                                ):
                                    self.tx_table.rows = list(self.backend.tx_messages)
                                    self.tx_table.update()
                                    ui.notify(f"Sent 0x{arb_id:X}", color="positive")
                                else:
                                    ui.notify("Tx Failed: Interface disconnected", color="negative")
                            except Exception as err:
                                ui.notify(f"Tx Error: {err}", color="negative")

                        ui.button("Send", on_click=handle_send).props(
                            "color=primary icon=send dense no-caps"
                        ).classes("px-4")


    def toggle_split_orientation(self):
        self.is_horizontal = not self.is_horizontal
        self.splitter._props["horizontal"] = self.is_horizontal
        self.splitter.value = 50

        if self.is_horizontal:
            self.split_btn.text = "Split: Top / Bottom"
            self.split_btn.props("icon=vertical_split")
        else:
            self.split_btn.text = "Split: Left / Right"
            self.split_btn.props("icon=horizontal_split")

        self.splitter.update()

    def refresh_rx(self):
        self.rx_table.rows = list(self.backend.rx_messages[:100])
        self.rx_counter_lbl.text = f"{self.backend.rx_count} frames"
        self.rx_table.update()

    def clear(self):
        self.rx_table.rows = []
        self.tx_table.rows = []
        self.rx_counter_lbl.text = "0 frames"
        self.rx_table.update()
        self.tx_table.update()