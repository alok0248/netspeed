from PyQt5 import QtWidgets, QtGui, QtCore

def start_tray(app, overlay):
    # Create tray icon
    tray_icon = QtWidgets.QSystemTrayIcon(app)
    
    # Create a simple icon
    icon_pixmap = QtGui.QPixmap(64, 64)
    icon_pixmap.fill(QtCore.Qt.black)
    painter = QtGui.QPainter(icon_pixmap)
    painter.setBrush(QtGui.QColor("#00FF00"))
    painter.drawRect(16, 16, 32, 32)
    painter.end()
    tray_icon.setIcon(QtGui.QIcon(icon_pixmap))
    tray_icon.setToolTip("NetSpeed Monitor")
    
    # Create context menu
    menu = QtWidgets.QMenu()
    
    show_action = menu.addAction("Show Overlay")
    show_action.triggered.connect(overlay.show)
    
    hide_action = menu.addAction("Hide Overlay")
    hide_action.triggered.connect(overlay.hide)
    
    menu.addSeparator()
    
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(menu)
    
    # Show tray icon
    tray_icon.show()
    
    return tray_icon
