import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem,
    QToolBar, QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit, QDialog, 
    QLabel, QLineEdit, QPushButton, QHeaderView, QSizePolicy, QFileDialog, 
    QComboBox
)
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtCore import Qt, QSize

from models import Site, Log, CustomDate, Tariff, LogType
from hashmap import HashMap
from engine import DataEngine, parse_date_range, is_valid_domain, is_valid_time_hms

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def icon(name: str) -> QIcon:
    return QIcon(os.path.join(CURRENT_DIR, "icons", name))


def apply_theme(app: QApplication):
    app.setStyleSheet("""
        QWidget { 
            background-color: #ffffff; 
            color: #1a1a1a; 
            font-family: 'Segoe UI', sans-serif; 
            font-size: 10pt; 
        }
        QMainWindow, QDialog { 
            background-color: #ffffff; 
        }
        QToolBar { 
            background-color: #f5f5f5; 
            border-bottom: 1px solid #cccccc; 
            spacing: 6px; 
            padding: 4px; 
        }
        QToolBar::separator { 
            background-color: #cccccc; 
            width: 1px; 
            margin-top: 4px; 
            margin-bottom: 4px; 
        }
        QTableWidget { 
            background-color: #ffffff; 
            border: 1px solid #cccccc; 
            gridline-color: #e8e8e8; 
            selection-background-color: #e6f0fa;
            selection-color: #000000; 
            outline: none;       
        }
        QTableWidget::item:hover { 
            background-color: #f2f7fc;      
            color: #000000;
        }
        QTableWidget::item:selected {
            background-color: #e6f0fa;
            color: #000000;
        }
        QHeaderView::section { 
            background-color: #666666; 
            color: #ffffff; 
            padding: 6px; 
            border: 1px solid #555555; 
            font-weight: bold; 
        }
        QLineEdit { 
            background-color: #ffffff; 
            border: 1px solid #999999; 
            border-radius: 4px; 
            padding: 4px; 
            color: #1a1a1a; 
        }
        QLineEdit:focus { 
            border: 1px solid #1a1a1a; 
        }
        QPushButton { 
            background-color: #333333; 
            color: #ffffff; 
            border: none; 
            border-radius: 4px; 
            padding: 6px 12px; 
            font-weight: bold; 
        }
        QPushButton:hover { 
            background-color: #4d4d4d; 
        }
        QPushButton:pressed { 
            background-color: #1a1a1a; 
        }
        QTextEdit { 
            background-color: #fafafa; 
            border: 1px solid #cccccc; 
            border-radius: 4px; 
            color: #1a1a1a;
        }
        QToolTip { 
            background-color: #ffffff; 
            color: #333333; 
            border: 1px solid #999999; 
        }
    """)


def fill_table_row(table: QTableWidget, row: int, values) -> None:
    table.insertRow(row)
    for col, value in enumerate(values):
        table.setItem(row, col, QTableWidgetItem(str(value)))


class InitDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Initialization")
        self.setFixedSize(350, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        self.size_input = QLineEdit("10")
        self.btn = QPushButton("Launch System")
        self.btn.clicked.connect(self.validate_and_accept)

        layout.addWidget(QLabel("Enter initial size for Sites Hash Table:"))
        layout.addWidget(self.size_input)
        layout.addWidget(self.btn)

    def validate_and_accept(self):
        try:
            val = int(self.size_input.text())
        except ValueError:
            val = 10

        if val < HashMap.MIN_CAPACITY:
            QMessageBox.warning(
                self, 
                "Capacity Warning", 
                f"Requested size ({val}) is lower than the minimum allowable size ({HashMap.MIN_CAPACITY}).\n"
                f"The system will be initiated with a capacity of {HashMap.MIN_CAPACITY}."
            )
        self.accept()

    def get_size(self) -> int:
        try:
            val = int(self.size_input.text())
            return max(val, HashMap.MIN_CAPACITY)
        except ValueError:
            return HashMap.MIN_CAPACITY


class AddSiteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Site")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("example.com")
        self.owner_input = QLineEdit()
        
        self.tariff_input = QComboBox()
        for t in Tariff:
            self.tariff_input.addItem(t.name)
            
        layout.addWidget(QLabel("Domain:"))
        layout.addWidget(self.domain_input)
        layout.addWidget(QLabel("Owner:"))
        layout.addWidget(self.owner_input)
        layout.addWidget(QLabel("Tariff:"))
        layout.addWidget(self.tariff_input)
        
        self.btn_ok = QPushButton("Add")
        self.btn_ok.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_ok)
        
        self.setLayout(layout)

    def validate_and_accept(self):
        if not self.domain_input.text().strip() or not self.owner_input.text().strip():
            QMessageBox.warning(self, "Error", "All fields must be filled")
            return
        if not is_valid_domain(self.domain_input.text().strip()):
            QMessageBox.warning(self, "Error", "Invalid domain")
            return
        self.accept()

    def get_data(self):
        return (
            self.domain_input.text().strip(),
            self.owner_input.text().strip(),
            self.tariff_input.currentText()
        )


class AddLogDialog(QDialog):
    def __init__(self, parent=None, default_domain=""):
        super().__init__(parent)
        self.setWindowTitle("Add Log")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        
        self.domain_input = QLineEdit(default_domain)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("24 apr 2026")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("14:22:00")
        
        self.type_input = QComboBox()
        for lt in LogType:
            self.type_input.addItem(lt.name)
            
        self.msg_input = QTextEdit()
        
        layout.addWidget(QLabel("Domain:"))
        layout.addWidget(self.domain_input)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("Time:"))
        layout.addWidget(self.time_input)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(self.type_input)
        layout.addWidget(QLabel("Message:"))
        layout.addWidget(self.msg_input)
        
        self.btn_ok = QPushButton("Add")
        self.btn_ok.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_ok)
        
        self.setLayout(layout)

    def validate_and_accept(self):
        if not all([self.domain_input.text().strip(), self.date_input.text().strip(), 
                    self.time_input.text().strip(), self.msg_input.toPlainText().strip()]):
            QMessageBox.warning(self, "Error", "All fields must be filled")
            return
        if not is_valid_domain(self.domain_input.text().strip()):
            QMessageBox.warning(self, "Error", "Invalid domain")
            return
        if not is_valid_time_hms(self.time_input.text().strip()):
            QMessageBox.warning(self, "Error", "Invalid time format. Strict HH:MM:SS required.")
            return
        try:
            CustomDate(self.date_input.text().strip())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid date format: {e}")
            return
        self.accept()

    def get_data(self):
        return (
            self.domain_input.text().strip(),
            self.date_input.text().strip(),
            self.time_input.text().strip(),
            self.type_input.currentText(),
            self.msg_input.toPlainText().strip()
        )


class HashDebugWindow(QDialog):
    def __init__(self, engine: DataEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Sites HashTable Debug")
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>SITES HASH MAP DEBUG INFO</b>"))

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont("Consolas", 10))
        self.debug_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; 
                color: #1a1a1a; 
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.debug_text)

        self.refresh_debug_info()

    def refresh_debug_info(self):
        sections = [
            "Sites Array Content:",
            "\n".join(f"Index [{i}]: {s.domain} | {s.owner} | {s.tariff}"
                      for i, s in enumerate(self.engine.sites_array)),
            "\nHash Map Structure & Collisions:",
            self.engine.sites_db.print_debug(),
        ]
        self.debug_text.setPlainText("\n".join(sections))


class TreeDebugWindow(QDialog):
    def __init__(self, engine: DataEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Logs Red-Black Trees Debug")
        self.resize(650, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>LOGS RED-BLACK TREES DEBUG INFO</b>"))

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont("Consolas", 10))
        self.debug_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; 
                color: #1a1a1a; 
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.debug_text)

        self.refresh_debug_info()

    def refresh_debug_info(self):
        sections = [
            "Logs Array Content:",
            "\n".join(f"Index [{i}]: {l.domain} | {l.date} | {l.time} | {l.type}"
                      for i, l in enumerate(self.engine.logs_array)),
            "\nRed-Black Tree (By Domain):",
            self.engine.logs_db.get_preorder_debug_string(),
            "\nRed-Black Tree (By Date):",
            self.engine.logs_by_date_db.get_preorder_debug_string(),
        ]
        self.debug_text.setPlainText("\n".join(sections))


class LogsWindow(QWidget):
    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.domain = None
        self.setWindowTitle("Domain Logs")
        self.resize(855, 450)

        layout = QVBoxLayout(self)
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)

        self.toolbar.addWidget(QLabel(" Search Domain: "))
        self.search_input = QLineEdit()
        self.search_input.setFixedWidth(150)
        self.search_input.setPlaceholderText("example.com")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.toolbar.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_tree_search)
        self.toolbar.addWidget(self.search_btn)

        self._add_toolbar_action("Add Log", self.add_log)
        self._add_toolbar_action("Delete Log", self.delete_log)
        self.toolbar.addSeparator()
        
        self._add_toolbar_action("Save Logs", self.save_logs)
        self._add_toolbar_action("Load Logs", self.load_logs_file)
        self.toolbar.addSeparator()

        debug_action = QAction(icon("debug.png"), "Debug Trees", self)
        debug_action.triggered.connect(self.open_tree_debug)
        self.toolbar.addAction(debug_action)

        self.steps_label = QLabel("Enter domain and click Search to see metrics...")
        self.steps_label.setStyleSheet("color: #52b788; font-weight: bold; padding-left: 10px;")
        layout.addWidget(self.steps_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Domain", "Date", "Time", "Type", "Message", "ArrayIdx"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(5, True)
        layout.addWidget(self.table)

        self.refresh_current_view()

    def _add_toolbar_action(self, label: str, handler) -> QAction:
        action = QAction(label, self)
        action.triggered.connect(handler)
        self.toolbar.addAction(action)
        return action

    def refresh_current_view(self):
        """Универсальный метод обновления таблицы согласно текущему тексту в поиске"""
        current_search = self.search_input.text().strip()
        self.load_logs_for_domain(current_search)

    def set_domain(self, domain: str):
        """Метод для внешнего управления (например, при клике в главном окне)"""
        self.domain = domain
        self.search_input.blockSignals(True)
        self.search_input.setText(domain)
        self.search_input.blockSignals(False)
        self.load_logs_for_domain(domain)

    def on_search_text_changed(self, text: str):
        if not text.strip():
            self.load_logs_for_domain("") 

    def perform_tree_search(self):
        target_domain = self.search_input.text().strip()
        self.load_logs_for_domain(target_domain)

    def load_logs_for_domain(self, domain: str):
        self.table.setRowCount(0)
        engine = self.main_window.engine
        
        if not domain.strip():
            self.steps_label.setText(f"Showing all available logs ({len(engine.logs_array)} records).")
            for i, log in enumerate(engine.logs_array):
                fill_table_row(self.table, i, [log.domain, log.date, log.time, log.type, log.message, i])
            return

        node, steps = engine.logs_db.search(domain)
        
        if node:
            indices_str = ", ".join(str(i) for i in node.indices_list)
            self.steps_label.setText(
                f"RBT Search Success: '{domain}' found in {steps} steps. Array Indices: [{indices_str}]"
            )
            
            row = 0
            for i in node.indices_list:
                log = engine.logs_array[i]
                fill_table_row(self.table, row, [log.domain, log.date, log.time, log.type, log.message, i])
                row += 1
        else:
            self.steps_label.setText(f"RBT Search: '{domain}' NOT found ({steps} steps evaluated).")

    def add_log(self):
        default_domain = self.search_input.text().strip()
        dialog = AddLogDialog(default_domain=default_domain, parent=self)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        domain, date_str, time_str, log_type, message = dialog.get_data()

        try:
            if self.main_window.engine.sites_db.search(domain).value is None:
                QMessageBox.critical(self, "Error", f"Site with domain '{domain}' does not exist!")
                return

            self.main_window.engine.insert_log(Log(domain, date_str, time_str, log_type, message))
            
            self.refresh_current_view()

            QMessageBox.information(
                self, 
                "Success", 
                f"New log record for domain '{domain}' has been successfully added."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add log: {e}")

    def delete_log(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection", "Select a log record in the table to delete")
            return

        target_idx = int(self.table.item(current_row, 5).text())
        log_to_delete = self.main_window.engine.logs_array[target_idx]

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this log record for '{log_to_delete.domain}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            self.main_window.engine.remove_log_at_index(target_idx)
            
            self.refresh_current_view()
            QMessageBox.information(self, "Success", "Log record successfully deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete log: {e}")

    def save_logs(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Logs", "", "Text Files (*.txt)")
        if filepath:
            try:
                self.main_window.engine.save_logs_to_file(filepath)
                QMessageBox.information(self, "Success", f"Saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def load_logs_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Logs", "", "Text Files (*.txt)")
        if filepath:
            try:
                self.main_window.engine.load_logs_from_file(filepath)
                # Обновляем вид согласно текущему фильтру
                self.refresh_current_view()
                QMessageBox.information(self, "Success", "Logs loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", str(e))

    def open_tree_debug(self):
        TreeDebugWindow(self.main_window.engine, self).exec()


class ReportWindow(QDialog):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Advanced Report Filter")
        
        self.resize(1100, 500)

        layout = QVBoxLayout(self)
        
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Tariff:"))
        self.tariff_combo = QComboBox()
        self.tariff_combo.addItem("All Tariffs", None)
        for t in Tariff:
            self.tariff_combo.addItem(str(t), t)
        filter_layout.addWidget(self.tariff_combo)

        filter_layout.addWidget(QLabel("Log Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", None)
        for lt in LogType:
            self.type_combo.addItem(str(lt), lt)
        filter_layout.addWidget(self.type_combo)

        filter_layout.addWidget(QLabel("From:"))
        self.start_input = QLineEdit("01 jan 2024")
        self.start_input.setFixedWidth(85)
        filter_layout.addWidget(self.start_input)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_input = QLineEdit("31 dec 2026")
        self.end_input.setFixedWidth(85)
        filter_layout.addWidget(self.end_input)

        filter_layout.addStretch(1)

        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.build_report)
        filter_layout.addWidget(self.generate_btn)

        filter_layout.addSpacing(15)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet("background-color: #666666;") 
        self.exit_btn.clicked.connect(self.close)
        filter_layout.addWidget(self.exit_btn)
        
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Domain", "Owner", "Tariff", "Date", "Time", "Type", "Message"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.build_report()

    def build_report(self) -> None:
        self.table.setRowCount(0)
        engine = self.main_window.engine
        
        target_tariff_enum = self.tariff_combo.currentData()
        target_type_enum = self.type_combo.currentData()

        try:
            start_dt, end_dt = parse_date_range(self.start_input.text(), self.end_input.text())
        except ValueError as e:
            QMessageBox.critical(self, "Date Error", str(e))
            return

        groups: dict[CustomDate, list[tuple[Site, Log]]] = {}
        for idx in engine.logs_by_date_db.get_logs_in_range(start_dt, end_dt):
            log = engine.logs_array[idx]
            
            site_res = engine.sites_db.search(log.domain)
            if site_res.value is None:
                continue
            site = engine.sites_array[site_res.value]
            
            if target_type_enum is not None and log.type != target_type_enum:
                continue
            
            if target_tariff_enum is not None and site.tariff != target_tariff_enum:
                continue
                

            date_key = log.date
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append((site, log))

        row = 0
        for date_key in sorted(groups.keys()):
            current_logs = sorted(groups[date_key], key=lambda x: (x[1].type, x[0].domain))
            for site, log in current_logs:
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(site.domain))
                self.table.setItem(row, 1, QTableWidgetItem(site.owner))
                self.table.setItem(row, 2, QTableWidgetItem(str(site.tariff)))
                self.table.setItem(row, 3, QTableWidgetItem(str(log.date)))
                self.table.setItem(row, 4, QTableWidgetItem(log.time))
                self.table.setItem(row, 5, QTableWidgetItem(str(log.type)))
                self.table.setItem(row, 6, QTableWidgetItem(log.message))
                row += 1


class MainWindow(QMainWindow):
    def __init__(self, initial_capacity: int):
        super().__init__()
        self.setWindowTitle("Virtual Hosting - Sites")
        self.resize(950, 500)

        self.engine = DataEngine(initial_capacity)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self._build_toolbar()

        self.search_status_label = QLabel("HashMap Search Metrics: Ready")
        self.search_status_label.setStyleSheet("font-weight: bold; color: #52b788;")
        main_layout.addWidget(self.search_status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Domain (Key)", "Owner", "Tariff"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemClicked.connect(self.table_row_selected)
        main_layout.addWidget(self.table)

        self.setCentralWidget(main_widget)
        self.refresh_table()

        self.logs_window = LogsWindow(self)
        self.move(50, 200)
        self.logs_window.move(1010, 200)

    def _build_toolbar(self):
        self.toolbar = QToolBar("Operations")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)

        actions = [
            ("Add Site", icon("add.png"), self.add_site, Qt.ToolButtonStyle.ToolButtonTextBesideIcon),
            ("Delete Site", icon("delete.png"), self.delete_site, Qt.ToolButtonStyle.ToolButtonTextBesideIcon),
        ]
        for label, action_icon, handler, style in actions:
            action = QAction(action_icon, label, self)
            action.triggered.connect(handler)
            self.toolbar.addAction(action)
            self.toolbar.widgetForAction(action).setToolButtonStyle(style)
        self.toolbar.addSeparator()

        save_action = QAction("Save Sites", self)
        save_action.triggered.connect(self.save_data)
        self.toolbar.addAction(save_action)
        
        load_action = QAction("Load Sites", self)
        load_action.triggered.connect(self.load_data)
        self.toolbar.addAction(load_action)
        self.toolbar.addSeparator()

        report_action = QAction("Generate Report", self)
        report_action.triggered.connect(self.open_report)
        self.toolbar.addAction(report_action)
        self.toolbar.addSeparator()

        self.toolbar.addWidget(QLabel(" Search Domain: "))
        self.domain_search_input = QLineEdit()
        self.domain_search_input.setFixedWidth(140)
        self.domain_search_input.setPlaceholderText("example.com")
        self.domain_search_input.textChanged.connect(self.on_search_text_changed)
        self.toolbar.addWidget(self.domain_search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_hash_search)
        self.toolbar.addWidget(self.search_btn)
        self.toolbar.addSeparator()

        debug_action = QAction(icon("debug.png"), "Debug Hash", self)
        debug_action.triggered.connect(self.open_hash_debug)
        self.toolbar.addAction(debug_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.toolbar.addAction(exit_action)

    def refresh_table(self):
        self.table.setRowCount(0)
        row = 0
        for site in self.engine.sites_array:
            fill_table_row(self.table, row, [site.domain, site.owner, site.tariff])
            row += 1

    def show_all_rows(self):
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def on_search_text_changed(self, text: str):
        if not text.strip():
            self.show_all_rows()
            self.search_status_label.setText("HashMap Search Metrics: Ready")
            self.table.clearSelection()
            self.logs_window.search_input.clear()
            self.logs_window.table.setRowCount(0)

    def perform_hash_search(self):
        target_domain = self.domain_search_input.text().strip()
        if not target_domain:
            self.show_all_rows()
            self.search_status_label.setText("HashMap Search Metrics: Ready")
            return

        search_res = self.engine.sites_db.search(target_domain)
        
        if search_res.value is not None:
            array_idx = search_res.value
            self.search_status_label.setText(
                f"HashMap Search Success: '{target_domain}' maps to array index [{array_idx}] found in {search_res.steps} steps."
            )
            
            for row in range(self.table.rowCount()):
                row_domain = self.table.item(row, 0).text()
                if row_domain == target_domain:
                    self.table.setRowHidden(row, False)
                    self.table.setCurrentCell(row, 0)
                else:
                    self.table.setRowHidden(row, True)
            
            self.logs_window.set_domain(target_domain)
        else:
            self.search_status_label.setText(
                f"HashMap Search: '{target_domain}' NOT found ({search_res.steps} steps evaluated)."
            )
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, True)
                
            self.logs_window.table.setRowCount(0)
            self.logs_window.steps_label.setText("RBT Search: Site not found in HashMap.")

    def table_row_selected(self, item):
        domain = self.table.item(item.row(), 0).text()
        search_res = self.engine.sites_db.search(domain)
        self.search_status_label.setText(
            f"Table Click Lookup: '{domain}' index is [{search_res.value}] found in {search_res.steps} steps.")
        self.logs_window.set_domain(domain)

    def add_site(self):
        dialog = AddSiteDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        domain, owner, tariff = dialog.get_data()

        try:
            if not is_valid_domain(domain):
                QMessageBox.warning(self, "Invalid Domain", f"'{domain}' is not a valid domain name")
                return 
            if self.engine.sites_db.search(domain).value is not None:
                QMessageBox.warning(self, "Duplicate", "Site with this domain already exists")
                return

            self.engine.insert_site(Site(domain, owner, tariff))
            self.refresh_table()
            QMessageBox.information(self, "Success", f"Site {domain} was successfully added.")
            self.domain_search_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add data: {e}")

    def delete_site(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection", "Select a row to delete")
            return

        domain = self.table.item(current_row, 0).text()

        node, _ = self.engine.logs_db.search(domain)
        has_logs = node is not None and node.indices_list.head is not None

        if has_logs:
            reply = QMessageBox.question(
                self, "Confirm Cascading Delete",
                f"Warning: The site '{domain}' contains log data.\n"
                f"Deleting this site will permanently erase all associated logs.\n"
                f"Do you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete the site '{domain}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.logs_window.search_input.text().strip() == domain:
             self.logs_window.search_input.clear()

        self.engine.remove_site_with_logs(domain)
        self.refresh_table()
        
        self.logs_window.refresh_current_view()
        
        self.domain_search_input.clear()
        self.search_status_label.setText("HashMap Search Metrics: Ready")
        QMessageBox.information(self, "Success", f"Site {domain} and all its logs were deleted.")

    def save_data(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Sites Directory", "", "Text Files (*.txt);;All Files (*)"
        )
        if not filepath:
            return
        try:
            self.engine.save_sites_to_file(filepath)
            QMessageBox.information(self, "Success", f"Sites directory saved to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")

    def load_data(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Sites Directory", "", "Text Files (*.txt);;All Files (*)"
        )
        if not filepath:
            return
        try:
            # Движок сам разберется, какие логи оставить, а какие удалить
            self.engine.load_sites_from_file(filepath)
            
            self.domain_search_input.clear()
            self.refresh_table()
            self.logs_window.refresh_current_view() # Обновляем окно логов
            
            QMessageBox.information(self, "Success", "Sites loaded. Logs for existing domains preserved.")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed: {e}")

    def open_report(self):
        ReportWindow(self).exec()

    def open_hash_debug(self):
        HashDebugWindow(self.engine, self).exec()

    def closeEvent(self, event):
        self.logs_window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    init_dialog = InitDialog()
    if init_dialog.exec() == QDialog.DialogCode.Accepted:
        main_win = MainWindow(init_dialog.get_size())
        main_win.show()
        main_win.logs_window.show()
        sys.exit(app.exec())