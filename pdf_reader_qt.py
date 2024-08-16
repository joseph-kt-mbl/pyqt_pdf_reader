import sys
from PyQt5.QtWidgets import (QShortcut, QApplication, QMainWindow, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, 
                             QVBoxLayout, QPushButton, QLabel, QScrollArea, QToolBar, QFileDialog)
from PyQt5.QtGui import QFont, QImage, QPixmap, QKeySequence, QIcon
from PyQt5.QtCore import Qt, QSize, QObject, QEvent

import fitz  # PyMuPDF

class KeyEventFilter(QObject):
    def __init__(self, prev_callback, next_callback):
        super().__init__()
        self.prev_callback = prev_callback
        self.next_callback = next_callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_PageDown:
                self.next_callback()
                return True
            elif event.key() == Qt.Key_PageUp:
                self.prev_callback()
                return True
        return super().eventFilter(obj, event)

class EdgeStylePDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Edge-Style PDF Reader')
        self.setGeometry(100, 100, 900, 700)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create button toolbar
        self.button_toolbar = QToolBar("Button Toolbar", self)
        self.button_toolbar.setIconSize(QSize(24, 24))  # Adjusted icon size
        self.button_toolbar.setStyleSheet("background-color: black; padding: 5px")
        self.addToolBar(Qt.TopToolBarArea, self.button_toolbar)

        # Open PDF button
        self.open_pdf_button = QPushButton("Open PDF")
        self.open_pdf_button.clicked.connect(self.open_pdf)
        self.style_open_pdf_button(self.open_pdf_button)
        self.button_toolbar.addWidget(self.open_pdf_button)

        # Previous Page button
        self.prev_page_button = QPushButton("Previous")
        self.prev_page_button.setIcon(QIcon('./UP.svg'))  # Adjust path if needed
        self.prev_page_button.setIconSize(QSize(24, 24))  # Adjusted icon size
        self.prev_page_button.clicked.connect(self.prev_page)
        self.style_nav_button(self.prev_page_button)
        self.button_toolbar.addWidget(self.prev_page_button)

        # Next Page button
        self.next_page_button = QPushButton("Next ")
        self.next_page_button.setIcon(QIcon('./arrow-down.svg'))  # Adjust path if needed
        self.next_page_button.setIconSize(QSize(24, 24))  # Adjusted icon size
        self.next_page_button.clicked.connect(self.next_page)
        self.style_nav_button(self.next_page_button)
        self.button_toolbar.addWidget(self.next_page_button)

        # Zoom In button
        self.zoom_in_button = QPushButton("Zoom In +")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.style_zoom_button(self.zoom_in_button)
        self.button_toolbar.addWidget(self.zoom_in_button)

        # Zoom Out button
        self.zoom_out_button = QPushButton("Zoom Out -")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.style_zoom_button(self.zoom_out_button)
        self.button_toolbar.addWidget(self.zoom_out_button)

        # Create indicators widget
        self.indicators_widget = QWidget()
        self.indicators_layout = QHBoxLayout(self.indicators_widget)
        self.indicators_layout.setContentsMargins(0, 0, 0, 0)
        self.indicators_layout.setSpacing(0)

        # Page counter
        self.page_counter = QLabel("Page: 0")
        self.page_counter.setFont(QFont('Arial', 12))
        self.indicators_layout.addWidget(self.page_counter)

        # Spacer
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.indicators_layout.addItem(self.spacer)

        # Zoom indicator
        self.zoom_indicator = QLabel("Zoom: 100%")
        self.zoom_indicator.setFont(QFont('Arial', 12))
        self.indicators_layout.addWidget(self.zoom_indicator)

        self.layout.addWidget(self.indicators_widget)

        # Create a QScrollArea for the PDF content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.pdf_view = QLabel()
        self.pdf_view.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.pdf_view)

        # Initialize PDF document
        self.doc = None
        self.current_page = 0
        self.zoom_factor = 1.0

        # Shortcuts
        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)

        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)

        # Install event filter for key events
        self.key_event_filter = KeyEventFilter(self.prev_page, self.next_page)
        self.installEventFilter(self.key_event_filter)

    def style_open_pdf_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 3px;
                padding: 10px 20px;
                font-size: 18px;
                font-weight: bold;
                margin: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def style_nav_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 18px;
                margin: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

    def style_zoom_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: black;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 18px;
                margin: 8px;
            }
            QPushButton:hover {
                background-color: #FFA000;
            }
        """)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_name:
            self.doc = fitz.open(file_name)
            self.current_page = 0
            self.render_page(self.current_page)

    def render_page(self, page_num):
        if self.doc is None:
            return

        if 0 <= page_num < self.doc.page_count:
            page = self.doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self.pdf_view.setPixmap(QPixmap.fromImage(image))
            self.page_counter.setText(f"Page: {page_num + 1} / {self.doc.page_count}")
            self.zoom_indicator.setText(f"Zoom: {int(self.zoom_factor * 100)}%")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.render_page(self.current_page)

    def next_page(self):
        if self.doc and self.current_page < self.doc.page_count - 1:
            self.current_page += 1
            self.render_page(self.current_page)

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.render_page(self.current_page)

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.render_page(self.current_page)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    reader = EdgeStylePDFReader()
    reader.show()
    sys.exit(app.exec_())
