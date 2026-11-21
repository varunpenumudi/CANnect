from nicegui import ui
from core.can_backend import CANBackend

BG_DARK = "#121820"
PANEL_DARK = "#1A222D"
BORDER_DARK = "#283548"

TRACE_COLUMNS = [
    {"name": "timestamp", "label": "Time (s)", "field": "timestamp", "align": "left", "sortable": True},
    {"name": "channel", "label": "Ch", "field": "channel", "align": "center"},
    {"name": "type", "label": "Dir", "field": "type", "align": "center"},
    {"name": "id", "label": "CAN ID", "field": "id", "align": "left", "sortable": True},
    {"name": "dlc", "label": "DLC", "field": "dlc", "align": "center"},
    {"name": "data", "label": "Data (Hex Payload)", "field": "data", "align": "left"},
]


class TraceTab:
    def __init__(self, backend: CANBackend):
        self.backend = backend
        # h-full + min-h-0 keeps the container locked inside main.py's workspace bounds
        self.container = ui.column().classes("w-full h-full min-h-0 gap-1 overflow-hidden")

        with self.container:
            # Resizable Top / Bottom Split (75% Top Trace Table, 25% Bottom Transmit Pane)
            self.splitter = (
                ui.splitter(horizontal=True, value=75)
                .classes("w-full flex-1 min-h-0")
                .style(f"background: {BG_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 4px;")
            )

            # ---------------- TOP PANE: UNIFIED BUS TRACE (RX & TX) ----------------
            with self.splitter.before:
                # overflow-hidden + min-h-0 forces children to scroll internally instead of expanding the pane
                with ui.column().classes("w-full h-full min-h-0 p-2 gap-1 overflow-hidden"):
                    with ui.row().classes("w-full items-center justify-between shrink-0"):
                        ui.label("BUS MESSAGE TRACE (RX / TX)").classes("text-xs font-bold text-emerald-400")
                        self.counter_lbl = ui.label("Rx: 0 | Tx: 0").classes("text-xs text-gray-400")

                    # rowsPerPage: 0 disables pagination so virtual-scroll handles all buffered rows smoothly.
                    # h-0 + flex-1 + sticky-header keeps the table strictly bounded to the top splitter pane.
                    self.trace_table = (
                        ui.table(
                            columns=TRACE_COLUMNS,
                            rows=[],
                            row_key="uid",
                            pagination={"rowsPerPage": 0},
                        )
                        .classes("w-full flex-1 h-0")
                        .props(
                            'dense flat bordered dark virtual-scroll '
                            ':virtual-scroll-item-size="28" '
                            ':virtual-scroll-sticky-size-start="28" '
                            'hide-bottom'
                        )
                    )

                    # Pin table header when scrolling through messages
                    ui.add_head_html("""
                    <style>
                        .q-table__middle thead tr th {
                            position: sticky;
                            top: 0;
                            z-index: 1;
                            background-color: #1A222D;
                        }
                    </style>
                    """)

                    # Color-code Tx (Blue) vs Rx (Green) in the 'type' column
                    self.trace_table.add_slot(
                        "body-cell-type",
                        r"""
                        <q-td :props="props">
                            <q-badge :color="props.value === 'Tx' ? 'blue-7' : 'emerald-7'" class="text-xs font-bold px-2">
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                        """,
                    )

            # ---------------- BOTTOM PANE: TRANSMIT MESSAGE (SEND PANE) ----------------
            with self.splitter.after:
                with ui.column().classes("w-full h-full min-h-0 p-2 gap-2 justify-center overflow-auto"):
                    ui.label("TRANSMIT MESSAGE (TX)").classes("text-xs font-bold text-blue-400")

                    with ui.row().style(
                        f"background: {PANEL_DARK}; border: 1px solid {BORDER_DARK}; border-radius: 4px;"
                    ).classes("w-full items-center gap-3 p-3"):
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
                                    # self.refresh_trace()
                                    ...
                                else:
                                    ui.notify("Tx Failed", color="negative")
                            except Exception as err:
                                ui.notify(f"Tx Error: {err}", color="negative")

                        tx_id.on("keydown.enter", handle_send)
                        tx_data.on("keydown.enter", handle_send)

                        ui.button("Send", on_click=handle_send).props(
                            "color=primary icon=send dense no-caps"
                        ).classes("px-4")

    def refresh_trace(self):
        self.trace_table.rows = list(self.backend.messages[:500])
        self.counter_lbl.text = f"Rx: {self.backend.rx_count} | Tx: {self.backend.tx_count}"
        self.trace_table.update()

    def clear(self):
        self.trace_table.rows = []
        self.counter_lbl.text = "Rx: 0 | Tx: 0"
        self.trace_table.update()