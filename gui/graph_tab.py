from nicegui import ui
from core.can_backend import CANBackend


class GraphTab:
    def __init__(self, backend: CANBackend):
        self.backend = backend
        self.container = (
            ui.column()
            .classes("w-full h-full p-4 items-center justify-center")
            .style("display: none;")
        )
        with self.container:
            ui.icon("show_chart", size="64px").classes("text-gray-500 mb-2")
            ui.label("Signal Graph View (SavvyCAN / BusMaster style)").classes(
                "text-lg font-bold text-gray-300"
            )
            ui.label("Plot time-series signals decoded from loaded DBC files.").classes(
                "text-xs text-gray-500"
            )