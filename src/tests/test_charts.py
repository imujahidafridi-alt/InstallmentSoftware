import pytest
from src.views.components.chart_widget import ChartWidget

def test_chart_widget_pie_zero_values(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    # This should execute without throwing Exception or division by zero warning
    widget.draw_chart(
        labels=["Completed", "Active"],
        values=[0, 0],
        title="Installment Completion Rate",
        chart_type="pie",
        theme="light"
    )
    # Check that it drew successfully and axes title matches
    assert widget.axes.get_title() == "Installment Completion Rate"

def test_chart_widget_pie_standard_values(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    widget.draw_chart(
        labels=["Completed", "Active"],
        values=[5, 10],
        title="Installment Completion Rate",
        chart_type="pie",
        theme="dark"
    )
    assert widget.axes.get_title() == "Installment Completion Rate"

def test_chart_widget_line_chart(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    widget.draw_chart(
        labels=["Jan", "Feb", "Mar"],
        values=[1000, 2000, 1500],
        title="Monthly Trend",
        chart_type="line",
        theme="light"
    )
    assert widget.axes.get_title() == "Monthly Trend"

def test_chart_widget_bar_chart(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    widget.draw_chart(
        labels=["Jan", "Feb", "Mar"],
        values=[5000, 8000, 6000],
        title="Outstanding Trend",
        chart_type="bar",
        theme="dark"
    )
    assert widget.axes.get_title() == "Outstanding Trend"


class MockEvent:
    def __init__(self, inaxes, xdata, ydata):
        self.inaxes = inaxes
        self.xdata = xdata
        self.ydata = ydata

def test_chart_widget_hover_line(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    widget.draw_chart(
        labels=["Jan", "Feb", "Mar"],
        values=[1000, 2000, 1500],
        title="Monthly Profit Trend (Rs.)",
        chart_type="line",
        theme="light"
    )
    
    # Hover over Feb (idx = 1)
    event = MockEvent(widget.axes, 1.0, 2000.0)
    widget._on_hover(event)
    
    assert widget.last_hovered_item == "Feb_2000"

def test_chart_widget_hover_out(qtbot):
    widget = ChartWidget()
    qtbot.addWidget(widget)
    
    widget.draw_chart(
        labels=["Jan", "Feb", "Mar"],
        values=[1000, 2000, 1500],
        title="Monthly Profit Trend (Rs.)",
        chart_type="line",
        theme="light"
    )
    
    # Hover over Feb (idx = 1)
    event = MockEvent(widget.axes, 1.0, 2000.0)
    widget._on_hover(event)
    assert widget.last_hovered_item == "Feb_2000"
    
    # Hover outside axes
    out_event = MockEvent(None, 1.0, 2000.0)
    widget._on_hover(out_event)
    assert widget.last_hovered_item is None
