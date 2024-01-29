# import datetime
import pandas as pd
import polars as pl

# from lightweight_charts import Chart
# from PySide6 import QtCore, QtWidgets, QtGui
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QLabel,
    QFileDialog,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from lightweight_charts.widgets import QtChart
import qdarktheme


class FileSelector(QWidget):
    def __init__(self):
        super().__init__()

        self.button = QPushButton("Select File")
        # self.button.setS
        self.filename_label = QLabel("File Name: ")
        self.text = QLabel("Please Select File")  # alignment=QtCore.Qt.AlignLeft)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.button, 1)
        self.layout.addStretch()
        self.layout.addWidget(self.filename_label, 1)
        self.layout.addWidget(self.text, 4)
        self.dialog = QFileDialog()
        self.selectedFile = None

        self.button.clicked.connect(self.select_file)

    @QtCore.Slot()
    def select_file(self):
        if self.dialog.exec():
            file = self.dialog.selectedFiles()[0]
            self.selectedFile = file
            self.text.setText(file)


class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.chart = QtChart(self)
        self.chart.legend(visible=True)
        # self.chart.topbar.textbox("symbol", "File")
        self.chart.topbar.switcher(
            "timeframe",
            ("2020", "2021", "2022", "2023", "all"),
            default="all",
            func=self.on_timeframe_selection,
        )
        self.line_ma20 = self.chart.create_line(
            "SMA20", color="rgba(175, 175, 175, 0.6)", width=1, price_line=False
        )
        self.line_upperband = self.chart.create_line(
            "BBandUpper", color="rgba(175, 20, 20, 0.6)", width=1, price_line=False
        )
        self.line_lowerband = self.chart.create_line(
            "BBandLower", color="rgba(20, 175, 20, 0.6)", width=1, price_line=False
        )
        self.file_selector = FileSelector()
        self.file_selector.button.clicked.connect(self.load_file)
        self.layout.addWidget(self.file_selector, 1)
        self.layout.addWidget(self.chart.get_webview(), 50)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.df = pl.DataFrame()

    @QtCore.Slot()
    def load_file(self):
        if self.file_selector.selectedFile:
            if self.file_selector.selectedFile.endswith(".csv"):
                self.df = pl.read_csv(self.file_selector.selectedFile)
            elif self.file_selector.selectedFile.endswith(".parquet"):
                self.df = pl.read_parquet(self.file_selector.selectedFile)
            else:
                raise ValueError("File type not supported")
            # df = pd.read_csv(self.file_selector.selectedFile)
            self.set_data(self.df)

    def set_data(self, df: pl.DataFrame):
        df = df.with_columns(pl.col("date").cast(str))
        self.chart.set(df.to_pandas(), render_drawings=True)

        df_bands = (
            df.with_columns(
                pl.col("close").rolling_mean(20).alias("SMA20"),
                pl.col("close").rolling_std(20).alias("STD20"),
            )
            .with_columns(
                (pl.col("SMA20") + 2 * pl.col("STD20")).alias("BBandUpper"),
                (pl.col("SMA20") - 2 * pl.col("STD20")).alias("BBandLower"),
            )
            .select(
                pl.col("date").alias("time"),
                pl.col("BBandUpper"),
                pl.col("SMA20"),
                pl.col("BBandLower"),
            )
        )
        self.line_ma20.set(df_bands.select(pl.col("time"), pl.col("SMA20")).to_pandas())
        self.line_upperband.set(
            df_bands.select(pl.col("time"), pl.col("BBandUpper")).to_pandas()
        )
        self.line_lowerband.set(
            df_bands.select(pl.col("time"), pl.col("BBandLower")).to_pandas()
        )

        if "LongShort" in df.columns:
            df_long = df.filter(
                pl.col("LongShort") == 1,
            ).select(pl.col("date"))
            for d in df_long["date"]:
                self.chart.marker(d, color="rgba(255, 0, 0, 0.7)", text="long")
            df_short = df.filter(
                pl.col("LongShort") == -1,
            ).select(pl.col("date"))
            for d in df_short["date"]:
                self.chart.marker(
                    d,
                    position="above",
                    shape="arrow_down",
                    color="rgba(0, 255, 0, 0.7)",
                    text="short",
                )

    def update_data(self, df: pl.DataFrame):
        self.chart.update(df.to_pandas())

    def on_timeframe_selection(self, chart: QtChart):
        if chart.topbar["timeframe"].value == "all":
            # df = pd.read_csv(self.file_selector.selectedFile)
            self.set_data(self.df)
        else:
            df = self.df.filter(
                pl.col("date").dt.year() == int(chart.topbar["timeframe"].value)#datetime.date()
            )
            self.set_data(df)
        # new_data = get_bar_data(chart.topbar["symbol"].value, chart.topbar["timeframe"].value)
        # if new_data.empty:
        #     return
        # chart.set(new_data, True)


if __name__ == "__main__":
    app = QApplication([])
    # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6"))
    qdarktheme.setup_theme()
    # qdarktheme.setup_theme("auto")
    window = QMainWindow()
    widget = ChartWidget()
    window.resize(800, 600)
    window.setCentralWidget(widget)
    window.setWindowTitle("Chart Viewer")
    window.show()
    app.exec()
