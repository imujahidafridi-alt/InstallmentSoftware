from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
from PyQt6.QtWidgets import QToolTip
from PyQt6.QtGui import QCursor

class ChartWidget(FigureCanvas):
    def __init__(self, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.current_chart_type = None
        self.current_labels = []
        self.current_values = []
        self.current_title = ""
        self.current_theme = "light"
        self.last_hovered_item = None
        self.mpl_connect('motion_notify_event', self._on_hover)

    def draw_chart(self, labels: list, values: list, title: str, chart_type: str = "line", theme: str = "dark"):
        """
        Plots the data using line or bar style, dynamically adjusting layout colors
        based on theme parameters.
        """
        try:
            self.current_chart_type = chart_type
            self.current_labels = labels
            self.current_values = values
            self.current_title = title
            self.current_theme = theme
            self.last_hovered_item = None

            self.axes.clear()
            
            # Color palettes matching QSS themes
            if theme == "dark":
                bg_color = "#1E1E1E"
                text_color = "#94A3B8"
                grid_color = "#2D2D2D"
                accent_color = "#3B82F6"  # Blue Accent
                bar_color = "#10B981"     # Emerald Green
            else:
                bg_color = "#FFFFFF"
                text_color = "#64748B"
                grid_color = "#F1F5F9"
                accent_color = "#2563EB"
                bar_color = "#10B981"

            # Apply figure and axes colors
            self.fig.patch.set_facecolor(bg_color)
            self.axes.set_facecolor(bg_color)
            
            # Plot data
            if chart_type == "line":
                self.axes.plot(labels, values, color=accent_color, marker='o', linewidth=2)
                self.axes.grid(True, color=grid_color, linestyle='--', linewidth=0.5)
                # Format currency formatting on Y-axis
                formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1000:.0f}k' if x >= 1000 else f'{x:.0f}')
                self.axes.yaxis.set_major_formatter(formatter)
            elif chart_type == "bar":
                self.axes.bar(labels, values, color=bar_color, width=0.5)
                self.axes.grid(True, color=grid_color, linestyle='--', linewidth=0.5)
                # Format currency formatting on Y-axis
                formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1000:.0f}k' if x >= 1000 else f'{x:.0f}')
                self.axes.yaxis.set_major_formatter(formatter)
            elif chart_type == "pie":
                if not values or sum(values) == 0:
                    self.axes.pie(
                        [1], 
                        labels=["No Data Available"], 
                        colors=["#94A3B8" if theme == "dark" else "#CBD5E1"], 
                        textprops={'color': text_color, 'fontsize': 8},
                        startangle=90, 
                        wedgeprops=dict(width=0.4, edgecolor=bg_color)
                    )
                else:
                    self.axes.pie(
                        values, 
                        labels=labels, 
                        autopct='%1.1f%%', 
                        colors=[bar_color, accent_color], 
                        textprops={'color': text_color, 'fontsize': 8},
                        startangle=90, 
                        wedgeprops=dict(width=0.4, edgecolor=bg_color)
                    )
                self.axes.grid(False)

            # Style layout parameters
            self.axes.set_title(title, fontsize=10, fontweight="bold", color=text_color, pad=10)
            self.axes.tick_params(axis='both', colors=text_color, labelsize=8)
            
            # Set borders (spines) invisible or matching grid color
            for spine in self.axes.spines.values():
                spine.set_color(grid_color)
                
            self.fig.tight_layout()
            self.draw()
        except Exception as e:
            print(f"Failed to draw chart '{title}': {e}")

    def _on_hover(self, event):
        if event.inaxes != self.axes:
            if self.last_hovered_item is not None:
                QToolTip.hideText()
                self.last_hovered_item = None
            return

        label = None
        val = None

        if self.current_chart_type in ("line", "bar"):
            if event.xdata is not None:
                try:
                    idx = int(round(event.xdata))
                except (ValueError, TypeError, OverflowError):
                    idx = -1
                if 0 <= idx < len(self.current_labels):
                    label = self.current_labels[idx]
                    val = self.current_values[idx]
        elif self.current_chart_type == "pie":
            for i, patch in enumerate(self.axes.patches):
                if patch.contains(event)[0]:
                    if i < len(self.current_labels):
                        label = self.current_labels[i]
                        val = self.current_values[i]
                    break

        if label is not None:
            hover_key = f"{label}_{val}"
            if self.last_hovered_item == hover_key:
                return
            self.last_hovered_item = hover_key

            title_clean = self.current_title
            # Format value nicely
            if "Rs." in self.current_title or "Profit" in self.current_title or "Collections" in self.current_title or "Outstanding" in self.current_title:
                from src.config import ConfigManager
                formatted_val = ConfigManager.format_currency(val)
            elif "%" in self.current_title or "Recovery" in self.current_title:
                formatted_val = f"{val:.1f}%"
            else:
                formatted_val = f"{val}"

            if self.current_chart_type == "pie":
                total_sum = sum(self.current_values)
                if total_sum > 0:
                    pct = (val / total_sum) * 100
                    tooltip_text = f"{title_clean}\n{label}: {formatted_val} ({pct:.1f}%)"
                else:
                    tooltip_text = f"{title_clean}\n{label}"
            else:
                tooltip_text = f"{title_clean}\n{label}: {formatted_val}"

            QToolTip.showText(QCursor.pos(), tooltip_text, self)
        else:
            if self.last_hovered_item is not None:
                QToolTip.hideText()
                self.last_hovered_item = None

