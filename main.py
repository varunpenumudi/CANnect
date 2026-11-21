import time
from nicegui import ui
from core.can_backend import CANBackend
from gui.connection_window import build_connection_dialog
from gui.graph_tab import GraphTab
from gui.trace_tab import TraceTab

BG_DARK = "#121820"
PANEL_DARK = "#1A222D"
BORDER_DARK = "#283548"

BODY_STYLE = f"background-color: {BG_DARK}; color: #ECEFF4; margin: 0; padding: 0; overflow: hidden; font-family: monospace, sans-serif;"
HEADER_STYLE = f"background: {PANEL_DARK}; border-bottom: 1px solid {BORDER_DARK}; height: 50px;"
FOOTER_STYLE = f"background: {PANEL_DARK}; border-top: 1px solid {BORDER_DARK}; height: 55px;"
MENU_STYLE = f"background-color: {PANEL_DARK}; color: #ECEFF4; border: 1px solid {BORDER_DARK};"

ui.dark_mode().enable()
ui.query("html").style("overflow: hidden;")
ui.query("body").style(BODY_STYLE)
ui.query(".nicegui-content").classes("p-0 m-0 gap-0").style("height: calc(100vh - 105px); overflow: hidden;")

backend = CANBackend()
active_window = "trace"

with ui.header().style(HEADER_STYLE).classes("items-center justify-between px-4"):
    with ui.row().classes("items-center gap-1"):
        ui.icon("directions_car", size="24px").classes("text-blue-400 mr-2")
        ui.label("CANalyzer UI").classes("font-bold text-white text-md mr-4")

        def handle_status_change(connected: bool, channel: str):
            if connected:
                conn_status_label.text = f"Connected: {channel}"
                conn_status_indicator.style("color: #4CAF50;")
            else:
                conn_status_label.text = "Disconnected"
                conn_status_indicator.style("color: #F44336;")

        conn_dialog = build_connection_dialog(backend, handle_status_change)

        with ui.button("Connection").props("flat dense no-caps text-color=white"):
            with ui.menu().style(MENU_STYLE):
                ui.menu_item("CAN Bus Setup...", on_click=conn_dialog.open)
                ui.menu_item(
                    "Disconnect Bus",
                    on_click=lambda: (
                        backend.disconnect(),
                        handle_status_change(False, ""),
                        ui.notify("CAN Interface closed", color="warning"),
                    ),
                )

        with ui.button("Tools").props("flat dense no-caps text-color=white"):
            with ui.menu().style(MENU_STYLE):
                ui.menu_item("Bus Load Monitor", on_click=lambda: ui.notify("Bus load stats running", color="info"))
                ui.menu_item("DBC Loader", on_click=lambda: ui.notify("Select DBC file", color="info"))

        with ui.button("View").props("flat dense no-caps text-color=white"):
            with ui.menu().style(MENU_STYLE):
                ui.menu_item("Trace Window", on_click=lambda: switch_window("trace"))
                ui.menu_item("Graph Window", on_click=lambda: switch_window("graph"))

        with ui.button("Help").props("flat dense no-caps text-color=white"):
            with ui.menu().style(MENU_STYLE):
                ui.menu_item("About CANalyzer", on_click=lambda: ui.notify("Open CAN Analyzer v1.0", color="info"))

        ui.separator().props("vertical").classes("mx-2 h-6")

        def action_start():
            if backend.is_connected:
                backend.is_running = True
                ui.notify("Trace listening resumed", color="positive")
            else:
                ui.notify("Please connect to a CAN bus first!", color="warning")

        def action_stop():
            backend.is_running = False
            ui.notify("Trace paused", color="grey")

        def action_clear():
            backend.messages.clear()
            trace_view.clear()
            ui.notify("Trace buffers cleared", color="info")

        ui.button(icon="play_arrow", on_click=action_start).props("flat dense round color=green-5").tooltip("Start Trace")
        ui.button(icon="pause", on_click=action_stop).props("flat dense round color=amber-5").tooltip("Stop Trace")
        ui.button(icon="delete_sweep", on_click=action_clear).props("flat dense round color=red-4").tooltip("Clear Buffers")

    with ui.row().classes("items-center gap-2"):
        conn_status_indicator = ui.icon("circle", size="12px").style("color: #F44336;")
        conn_status_label = ui.label("Disconnected").classes("text-xs text-gray-300 mr-2")

# Workspace Containers
with ui.column().classes("w-full p-2 flex-grow").style("height: 90vh"):
    trace_view = TraceTab(backend)
    graph_view = GraphTab(backend)

def switch_window(target: str):
    global active_window
    active_window = target
    trace_view.container.style(f"display: {'flex' if target == 'trace' else 'none'};")
    graph_view.container.style(f"display: {'flex' if target == 'graph' else 'none'};")
    btn_trace.props(f"color={'primary' if target == 'trace' else 'grey-9'}")
    btn_graph.props(f"color={'primary' if target == 'graph' else 'grey-9'}")

# Bottom Dock Switcher in main.py
with ui.footer().style(
    f"background: {PANEL_DARK}; border-top: 1px solid {BORDER_DARK}; min-height: 55px;"
).classes("items-center justify-between px-3 py-1"):
    with ui.row().classes("items-center gap-2"):
        btn_trace = ui.button("Trace", on_click=lambda: switch_window("trace")).props("dense no-caps size=md color=primary").classes("text-xs px-3 py-1")
        btn_graph = ui.button("Graph", on_click=lambda: switch_window("graph")).props("dense no-caps size=md color=grey-9").classes("text-xs px-3 py-1")

    with ui.row().classes("items-center gap-4 text-xs text-gray-400"):
        footer_rx = ui.label("Rx: 0 fps")
        footer_tx = ui.label("Tx: 0 fps")
        footer_err = ui.label("Errors: 0")


# Real-time Polling Loop
last_rx_count = 0
last_tx_count = 0
last_time = time.time()

def update_ui_loop():
    global last_rx_count, last_tx_count, last_time

    while backend.poll_rx():
        ...

    if active_window == "trace":
        trace_view.refresh_trace()

    now = time.time()
    dt = now - last_time
    if dt >= 1.0:
        footer_rx.text = f"Rx: {int((backend.rx_count - last_rx_count) / dt)} fps"
        footer_tx.text = f"Tx: {int((backend.tx_count - last_tx_count) / dt)} fps"
        footer_err.text = f"Errors: {backend.error_count}"
        last_rx_count = backend.rx_count
        last_tx_count = backend.tx_count
        last_time = now

ui.timer(0.01, update_ui_loop)
ui.run(native=True)