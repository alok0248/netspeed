from PyQt5 import QtWidgets, QtCore, QtGui

class SpeedOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
    QtCore.Qt.WindowStaysOnTopHint |
    QtCore.Qt.FramelessWindowHint |
    QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        self.setStyleSheet("background-color: rgba(0,0,0,180);")
        
        # drag handling
        self._drag_active = False
        self._drag_position = QtCore.QPoint()
        
        self.label = QtWidgets.QLabel("DL: 0.00 Mbps | UL: 0.00 Mbps | Today: 0.00 MB", self)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-family: Arial;
                font-size: 12pt;
            }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.adjustSize()
        # load saved position
        settings = QtCore.QSettings('NetSpeed', 'Overlay')
        pos = settings.value('pos')
        if pos:
            self.move(pos)
        else:
            screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
            self.move(screen.right() - self.width() - 10, 10)
        print(f"Overlay created at position: {self.pos()}, size: {self.size()}")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = False
            # save position
            settings = QtCore.QSettings('NetSpeed', 'Overlay')
            settings.setValue('pos', self.pos())
            event.accept()

    def update_text(self, dl, ul, total):
        dl_mbps = (dl * 8) / 1e6
        ul_mbps = (ul * 8) / 1e6
        total_mb = total / 1e6
        self.label.setText(
            f"\u2193 {dl_mbps:.2f} Mbps   \u2191 {ul_mbps:.2f} Mbps\nToday: {total_mb:.2f} MB")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.adjustSize()
        self.adjustSize()
