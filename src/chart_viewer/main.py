# import datetime
import pandas as pd
import polars as pl

# from lightweight_charts import Chart
from PySide6 import QtCore, QtWidgets, QtGui

# from PySide6 import QtCore
# from PyQt5 import QtCore
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QLabel,
    QFileDialog,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QDialog,
    QInputDialog,
    QFormLayout,
    QDialogButtonBox,
)
from lightweight_charts.widgets import QtChart
import qdarktheme


class S3SettingDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        f: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Dialog,
    ) -> None:
        super().__init__(parent, f)
        self.settings = dict(
            access_key_id=QLineEdit(""),
            secret_access_key=QLineEdit(""),
            region=QLineEdit(""),
            endpoint_url=QLineEdit(""),
        )
        self.layout = QFormLayout(self)  # QVBoxLayout()
        for k, v in self.settings.items():
            self.layout.addRow(f"{k}: ", v)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.read_settings()

        self.button_box.accepted.connect(self.write_settings)

    def get_settings(self):
        return {k: v.text() for k, v in self.settings.items()}

    def write_settings(self):
        store_settings = QtCore.QSettings()  # fileName="ChartViewer")
        store_settings.beginGroup("S3Setting")
        for k, v in self.settings.items():
            store_settings.setValue(k, v.text())
        store_settings.endGroup()

    def read_settings(self):
        store_settings = QtCore.QSettings()
        store_settings.beginGroup("S3Setting")
        for k, v in self.settings.items():
            v.setText(store_settings.value(k, ""))
        store_settings.endGroup()


class FileSelector(QWidget):
    file_selected = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.button = QPushButton("Select File")
        # self.button.setS
        self.filename_label = QLabel("File Name: ")
        # self.text = QLabel("Please Select File")  # alignment=QtCore.Qt.AlignLeft)
        self.filename = QLineEdit("Please Select File")
        self.filetype_box = QComboBox(self)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.button, 1)
        self.layout.addStretch()
        self.layout.addWidget(self.filetype_box, 1)
        self.layout.addWidget(self.filename_label, 0.5)
        self.layout.addWidget(self.filename, 4)
        # self.layout.addWidget(self.line_edit, 2)
        self.dialog = QFileDialog()
        self.selectedFile = None
        self.s3_setting = {}
        self.filename.setReadOnly(True)
        self.filetype_box.addItems(["local", "s3"])

        self.button.clicked.connect(self.select_local_file)
        self.filetype_box.activated.connect(self.select_filetype)
        # self.filetype_box.activated.connect(self.write_settings)
        self.filename.returnPressed.connect(self.set_selected_file)
        # self.read_settings()

    @QtCore.Slot()
    # @QtCore.pyqtSlot()
    def set_selected_file(self, f=None):
        if f:
            self.filename.setText(f)
        self.selectedFile = self.filename.text()
        print("emit")
        self.file_selected.emit()
        self.write_settings()

    @QtCore.Slot()
    # @QtCore.pyqtSlot()
    def select_local_file(self):
        if self.dialog.exec():
            file = self.dialog.selectedFiles()[0]
            # self.filename.setText(file)
            self.set_selected_file(file)

    @QtCore.Slot()
    # @QtCore.pyqtSlot()
    def setting(self):
        if self.dialog.exec():
            self.s3_setting = self.dialog.get_settings()

    def is_s3(self):
        return self.filetype_box.currentText() == "s3"

    def select_filetype(self):
        print(f"|{self.filetype_box.currentText()}|")
        if self.filetype_box.currentText() == "local":
            if self.filename.text() == "":
                self.filename.setText("Please Select File")
            self.dialog = QFileDialog()
            self.filename.setReadOnly(True)
            self.button.setText("Select File")
            self.button.clicked.disconnect(self.setting)
            self.button.clicked.connect(self.select_local_file)
            self.write_settings()
            # self.read_settings()
        else:
            if self.filename.text() == "Please Select File":
                # self.set_selected_file("")
                self.filename.setText("")
            self.dialog = S3SettingDialog()  # QInputDialog()
            self.button.setText("Setting")
            self.filename.setReadOnly(False)
            self.s3_setting = self.dialog.get_settings()
            self.button.clicked.disconnect(self.select_local_file)
            self.button.clicked.connect(self.setting)
            self.write_settings()
            # self.read_settings()

    def write_settings(self):
        store_settings = QtCore.QSettings()  # fileName="ChartViewer")
        store_settings.beginGroup("FileSelector")
        if self.selectedFile:
            store_settings.setValue("selectedFile", self.selectedFile)
            store_settings.setValue("filetype", self.filetype_box.currentText())
        print("write setting filetype: {}".format(store_settings.value("filetype", "")))
        store_settings.endGroup()

    def read_settings(self):
        store_settings = QtCore.QSettings()
        store_settings.beginGroup("FileSelector")
        print("read setting filetype: {}".format(store_settings.value("filetype", "local")))
        self.filetype_box.setCurrentText(store_settings.value("filetype", "local"))
        self.select_filetype()
        if not self.selectedFile:
            self.selectedFile = store_settings.value("selectedFile", None)
            # self.filename.setText(self.selectedFile)
            if self.selectedFile:
                self.set_selected_file(self.selectedFile)
        store_settings.endGroup()


class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.chart = QtChart(self)
        self.chart.candle_style(
            # up_color="rgba(200, 0, 0, 100)",
            # down_color="rgba(0, 200, 0, 100)",
            up_color="rgba(200, 97, 100, 100)",
            down_color="rgba(39, 157, 130, 100)",
        )
        self.chart.volume_config(
            up_color="rgba(200,127,130,0.8)", down_color="rgba(83,141,131,0.8)"
        )
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
        # self.file_selector.button.clicked.connect(self.load_file)
        self.file_selector.file_selected.connect(self.load_file)
        self.file_selector.read_settings()
        
        self.layout.addWidget(self.file_selector, 1)
        self.layout.addWidget(self.chart.get_webview(), 50)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.df = pl.DataFrame()
        # if self.file_selector.selectedFile:
        #     self.load_file()

    @QtCore.Slot()
    # @QtCore.pyqtSlot()
    def load_file(self):
        if self.file_selector.selectedFile:
            if self.file_selector.selectedFile.endswith(".csv"):
                self.df = pl.read_csv(
                    self.file_selector.selectedFile,
                    storage_options=self.file_selector.s3_setting
                    if self.file_selector.is_s3()
                    else {},
                )
            elif self.file_selector.selectedFile.endswith(".parquet"):
                print(self.file_selector.s3_setting)
                self.df = pl.read_parquet(
                    self.file_selector.selectedFile,
                    storage_options=self.file_selector.s3_setting
                    if self.file_selector.is_s3()
                    else {},
                )
            else:
                raise ValueError("File type not supported")
            # df = pd.read_csv(self.file_selector.selectedFile)
            self.set_data(self.df)

    def set_data(self, df: pl.DataFrame):
        self.chart.clear_markers()
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
            df_marker = df.filter(pl.col("LongShort").is_not_null())
            for d, pos in zip(df_marker["date"], df_marker["LongShort"]):
                if pos > 0:
                    self.chart.marker(
                        d, color="rgba(255, 0, 0, 0.7)", text=f"long: {pos}"
                    )
                else:
                    self.chart.marker(
                        d,
                        position="above",
                        shape="arrow_down",
                        color="rgba(0, 255, 0, 0.7)",
                        text=f"short: {pos}",
                    )

    def update_data(self, df: pl.DataFrame):
        self.chart.update(df.to_pandas())

    def on_timeframe_selection(self, chart: QtChart):
        if chart.topbar["timeframe"].value == "all":
            # df = pd.read_csv(self.file_selector.selectedFile)
            self.set_data(self.df)
        else:
            df = self.df.filter(
                pl.col("date").dt.year()
                == int(chart.topbar["timeframe"].value)  # datetime.date()
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
