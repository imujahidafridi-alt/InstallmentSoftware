from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

class ChartWidget(FigureCanvas):
    def __init__(self, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def draw_chart(self, labels: list, values: list, title: str, chart_type: str = "line", theme: str = "dark"):
        """
        Plots the data using line or bar style, dynamically adjusting layout colors
        based on theme parameters.
        """
        try:
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

