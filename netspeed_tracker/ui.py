import sys
import ctypes
from PyQt5 import QtWidgets, QtCore, QtGui
from netspeed_tracker.monitor import format_data_size, format_speed

# Windows API constants and functions
user32 = ctypes.windll.user32
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

class BandwidthLimitDialog(QtWidgets.QDialog):
    def __init__(self, current_limit_bytes, parent=None):
        super().__init__(parent)
        self.current_limit = current_limit_bytes
        self.new_limit = current_limit_bytes
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Set Bandwidth Limit')
        self.setFixedSize(400, 200)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info label
        info_label = QtWidgets.QLabel('Enter bandwidth limit in GB:')
        info_label.setStyleSheet('font-size: 12pt; font-weight: bold;')
        layout.addWidget(info_label)
        
        # Input field
        self.input_field = QtWidgets.QLineEdit()
        # Convert bytes to GB for initial value
        initial_gb = self.current_limit / (1024 * 1024 * 1024)
        self.input_field.setText(f'{initial_gb:.0f}')
        self.input_field.setStyleSheet('''
            QLineEdit {
                padding: 10px;
                font-size: 12pt;
                border: 2px solid #333;
                border-radius: 5px;
                background-color: #222;
                color: white;
            }
        ''')
        layout.addWidget(self.input_field)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        ok_button = QtWidgets.QPushButton('OK')
        ok_button.setStyleSheet('''
            QPushButton {
                background-color: #00ff00;
                color: black;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #00dd00;
            }
        ''')
        ok_button.clicked.connect(self.accept_dialog)
        button_layout.addWidget(ok_button)
        
        cancel_button = QtWidgets.QPushButton('Cancel')
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #555;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #777;
            }
        ''')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def accept_dialog(self):
        try:
            limit_gb = float(self.input_field.text())
            if limit_gb > 0:
                self.new_limit = int(limit_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
                self.accept()
            else:
                QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a positive number!')
        except ValueError:
            QtWidgets.QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid number!')
        
    def get_limit(self):
        return self.new_limit


class ColorSelectionPanel(QtWidgets.QDialog):
    def __init__(self, parent_overlay=None):
        super().__init__()
        self.settings = QtCore.QSettings('NetSpeed', 'Overlay')
        self.parent_overlay = parent_overlay
        self.init_ui()
        
    def set_parent_overlay(self, overlay):
        self.parent_overlay = overlay
        
    def init_ui(self):
        self.setWindowTitle('Theme Settings')
        self.setFixedSize(360, 260)
        self.setStyleSheet('''
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: 10pt;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff00;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
        ''')
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(12)
        
        title = QtWidgets.QLabel('Theme Settings')
        title.setStyleSheet('font-size: 14pt; font-weight: bold; color: #00ff00;')
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Opacity slider
        opacity_layout = QtWidgets.QHBoxLayout()
        opacity_label = QtWidgets.QLabel('Opacity:')
        opacity_label.setStyleSheet('font-size: 11pt;')
        opacity_layout.addWidget(opacity_label)
        self.opacity_value = QtWidgets.QLabel('70%')
        self.opacity_value.setStyleSheet('font-size: 11pt; color: #00ff00; font-weight: bold;')
        opacity_layout.addWidget(self.opacity_value)
        layout.addLayout(opacity_layout)
        
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.settings.value('opacity', 70, type=int)))
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        layout.addWidget(self.opacity_slider)
        
        # Background color button
        bg_layout = QtWidgets.QHBoxLayout()
        bg_layout.addWidget(QtWidgets.QLabel('Background Color:'))
        self.bg_button = QtWidgets.QPushButton()
        self.bg_button.setFixedSize(30, 30)
        self.bg_button.clicked.connect(self.choose_bg_color)
        bg_layout.addWidget(self.bg_button)
        bg_layout.addStretch()
        layout.addLayout(bg_layout)
        
        # Text color button
        text_layout = QtWidgets.QHBoxLayout()
        text_layout.addWidget(QtWidgets.QLabel('Text Color:'))
        self.text_button = QtWidgets.QPushButton()
        self.text_button.setFixedSize(30, 30)
        self.text_button.clicked.connect(self.choose_text_color)
        text_layout.addWidget(self.text_button)
        text_layout.addStretch()
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        close_button = QtWidgets.QPushButton('Close')
        close_button.setStyleSheet('''
            QPushButton {
                background-color: #555555;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        ''')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.load_colors()
        
    def load_colors(self):
        bg_color = self.settings.value('bg_color', '#000000', type=str)
        text_color = self.settings.value('text_color', '#00FF00', type=str)
        self.bg_button.setStyleSheet(f'background-color: {bg_color}; border: 1px solid #555555; border-radius: 4px;')
        self.text_button.setStyleSheet(f'background-color: {text_color}; border: 1px solid #555555; border-radius: 4px;')
        
    def update_opacity(self, value):
        self.opacity_value.setText(f'{value}%')
        self.settings.setValue('opacity', value)
        if self.parent_overlay:
            try:
                self.parent_overlay.apply_theme()
            except Exception as e:
                print(f"Error applying theme: {e}")
        
    def choose_bg_color(self):
        try:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                self.settings.setValue('bg_color', color.name())
                self.bg_button.setStyleSheet(f'background-color: {color.name()}; border: 1px solid #555555; border-radius: 4px;')
                if self.parent_overlay and hasattr(self.parent_overlay, 'apply_theme'):
                    self.parent_overlay.apply_theme()
        except Exception as e:
            print(f"Error choosing background color: {e}")
                
    def choose_text_color(self):
        try:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                self.settings.setValue('text_color', color.name())
                self.text_button.setStyleSheet(f'background-color: {color.name()}; border: 1px solid #555555; border-radius: 4px;')
                if self.parent_overlay and hasattr(self.parent_overlay, 'apply_theme'):
                    self.parent_overlay.apply_theme()
        except Exception as e:
            print(f"Error choosing text color: {e}")


class SpeedOverlay(QtWidgets.QWidget):
    def __init__(self, monitor=None):
        super().__init__()
        print("SpeedOverlay initializing...")
        self.settings = QtCore.QSettings('NetSpeed', 'Overlay')
        self.fixed = self.settings.value('fixed', False, type=bool)
        self.font_size = self.settings.value('font_size', 12, type=int)
        self.speed_unit = self.settings.value('speed_unit', 'Mbps', type=str)
        self.glass_theme = self.settings.value('glass_theme', False, type=bool)
        self.transparent_theme = self.settings.value('transparent_theme', False, type=bool)
        self.opacity = self.settings.value('opacity', 70, type=int)
        self.color_panel = None
        self.monitor = monitor  # Hold reference to NetMonitor for bandwidth limit
        
        # Dragging
        self.drag_active = False
        self.drag_start_pos = QtCore.QPoint()
        
        self.init_ui()
        
        # Restore position only
        if self.settings.contains('geometry'):
            saved_geometry = self.settings.value('geometry')
            temp_widget = QtWidgets.QWidget()
            temp_widget.restoreGeometry(saved_geometry)
            self.move(temp_widget.pos())
        else:
            self.move(100, 100)
            
        self.update_cursor()
        self.apply_theme()
        
        # Set initial text and adjust size
        dl_str = format_speed(0, self.speed_unit)
        ul_str = format_speed(0, self.speed_unit)
        today_total_str = format_data_size(0)
        self.label.setText(
            f"\u2193 {dl_str}   \u2191 {ul_str}\n"
            f"Today: {today_total_str}"
        )
        self.label.adjustSize()
        self.resize(self.label.size())
        self.label.setGeometry(0, 0, self.width(), self.height())
        
        print("Showing overlay...")
        self.show()
        self.raise_()
        self.activateWindow()
        print("Overlay should be visible now.")

    def init_ui(self):
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )
        
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setText("↓ 0.00 Mbps   ↑ 0.00 Mbps\nToday: 0.00 GB")
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        
        self.size_grip = QtWidgets.QSizeGrip(self)
        self.size_grip.setStyleSheet('background:transparent;')
        self.size_grip.resize(12, 12)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.ensure_topmost)
        self.timer.start(1000)
        
    def ensure_topmost(self):
        self.raise_()
        if hasattr(self, 'winId'):
            hwnd = int(self.winId())
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

    def apply_theme(self):
        bg_color = self.settings.value('bg_color', '#000000', type=str)
        text_color = self.settings.value('text_color', '#00FF00', type=str)
        opacity_val = self.settings.value('opacity', 70, type=int)
        
        # Convert hex color to RGBA
        def hex_to_rgba(hex_color, opacity):
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            # Parse RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Convert opacity to 0-255
            a = int(opacity * 2.55)
            return f'rgba({r}, {g}, {b}, {a})'
        
        print(f"Applying theme - glass: {self.glass_theme}, transparent: {self.transparent_theme}")
        
        if self.transparent_theme:
            # Fully transparent theme: no background at all
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.setWindowOpacity(1.0)
            self.label.setStyleSheet(f'''
                QLabel {{
                    background-color: transparent;
                    color: {text_color};
                    padding: 12px;
                    font-size: {self.font_size}pt;
                    font-weight: bold;
                }}
            ''')
        elif self.glass_theme:
            # Glass theme with semi-transparent black background and border
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.setWindowOpacity(1.0)
            self.label.setStyleSheet(f'''
                QLabel {{
                    background-color: rgba(0, 0, 0, {int(opacity_val * 2.55)});
                    color: {text_color};
                    padding: 12px;
                    font-size: {self.font_size}pt;
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, {int(opacity_val * 0.3)});
                    border-radius: 16px;
                }}
            ''')
        else:
            # Solid theme: uses custom background color with transparency
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.setWindowOpacity(1.0)
            self.label.setStyleSheet(f'''
                QLabel {{
                    background-color: {hex_to_rgba(bg_color, opacity_val)};
                    color: {text_color};
                    padding: 12px;
                    font-size: {self.font_size}pt;
                    font-weight: bold;
                    border-radius: 8px;
                }}
            ''')
        
        # Adjust size to fit text
        self.label.adjustSize()
        self.resize(self.label.size())
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.update_size_grip()
        
    def update_size_grip(self):
        self.size_grip.move(self.width() - 12, self.height() - 12)
        self.size_grip.raise_()
        
    def update_cursor(self):
        if self.fixed:
            self.setCursor(QtCore.Qt.ArrowCursor)
        else:
            self.setCursor(QtCore.Qt.SizeAllCursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self.fixed:
            self.drag_active = True
            self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_active and not self.fixed:
            # Calculate new position
            new_pos = event.globalPos() - self.drag_start_pos
            
            # Boundary constraints: allow anywhere on the full screen (including taskbar area)
            screen_geo = QtWidgets.QApplication.primaryScreen().geometry()  # Full screen geometry
            new_x = max(screen_geo.left(), min(new_pos.x(), screen_geo.right() - self.width()))
            new_y = max(screen_geo.top(), min(new_pos.y(), screen_geo.bottom() - self.height()))
            
            self.move(new_x, new_y)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_active = False
            self.settings.setValue('geometry', self.saveGeometry())
            self.settings.setValue('fixed', self.fixed)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_size_grip()
        self.label.setGeometry(0, 0, self.width(), self.height())

    def open_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        
        text_size_menu = menu.addMenu('Text Size')
        text_sizes = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 28, 32, 36, 40, 48, 56, 64, 72]
        for size in text_sizes:
            action = text_size_menu.addAction(f'{size} pt')
            action.setCheckable(True)
            if size == self.font_size:
                action.setChecked(True)
            action.triggered.connect(lambda checked, s=size: self.set_text_size(s))
        
        speed_unit_menu = menu.addMenu('Speed Unit')
        speed_units = ['B/s', 'Kbps', 'Mbps', 'Gbps']
        for unit in speed_units:
            action = speed_unit_menu.addAction(unit)
            action.setCheckable(True)
            if unit == self.speed_unit:
                action.setChecked(True)
            action.triggered.connect(lambda checked, u=unit: self.set_speed_unit(u))
            
        # Bandwidth limit submenu
        bw_menu = menu.addMenu('Bandwidth Limit')
        
        edit_limit_action = bw_menu.addAction('Edit Limit...')
        edit_limit_action.triggered.connect(self.open_bandwidth_dialog)
        
        # Theme menu
        theme_menu = menu.addMenu('Theme')
        
        solid_action = theme_menu.addAction('Solid Theme')
        solid_action.setCheckable(True)
        solid_action.setChecked(not self.glass_theme and not self.transparent_theme)
        solid_action.triggered.connect(lambda: self.set_theme('solid'))
        
        glass_action = theme_menu.addAction('Glass Theme')
        glass_action.setCheckable(True)
        glass_action.setChecked(self.glass_theme)
        glass_action.triggered.connect(lambda: self.set_theme('glass'))
        
        transparent_action = theme_menu.addAction('Transparent Theme')
        transparent_action.setCheckable(True)
        transparent_action.setChecked(self.transparent_theme)
        transparent_action.triggered.connect(lambda: self.set_theme('transparent'))
        
        color_panel_action = theme_menu.addAction('Theme Settings')
        color_panel_action.triggered.connect(self.toggle_color_panel)
        
        fix_label = 'Unlock Position' if self.fixed else 'Fix Position'
        fix_action = menu.addAction(fix_label)
        fix_action.triggered.connect(self.toggle_fix_position)
        
        menu.addSeparator()
        reset_action = menu.addAction('Reset to default setting')
        reset_action.triggered.connect(self.reset_to_default)
        
        exit_action = menu.addAction('Exit')
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        
        menu.setStyleSheet('''
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 6px;
            }
            QMenu::item {
                padding: 6px 22px;
            }
            QMenu::item:selected {
                background-color: #444;
                border-radius: 4px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #444;
                margin: 5px 10px;
            }
        ''')
        menu.exec_(self.mapToGlobal(pos))
        
    def set_text_size(self, size):
        self.font_size = size
        self.settings.setValue('font_size', size)
        self.apply_theme()
        # Adjust size for new font
        self.label.adjustSize()
        self.resize(self.label.size())
        self.label.setGeometry(0, 0, self.width(), self.height())
    
    def set_speed_unit(self, unit):
        self.speed_unit = unit
        self.settings.setValue('speed_unit', unit)
        # Adjust size for new unit text
        self.label.adjustSize()
        self.resize(self.label.size())
        self.label.setGeometry(0, 0, self.width(), self.height())
    
    def set_theme(self, theme):
        if theme == 'solid':
            self.glass_theme = False
            self.transparent_theme = False
        elif theme == 'glass':
            self.glass_theme = True
            self.transparent_theme = False
        elif theme == 'transparent':
            self.glass_theme = False
            self.transparent_theme = True
        self.settings.setValue('glass_theme', self.glass_theme)
        self.settings.setValue('transparent_theme', self.transparent_theme)
        self.apply_theme()
    
    def toggle_glass_theme(self):
        self.set_theme('glass')
    
    def toggle_transparent_theme(self):
        self.set_theme('transparent')
        
    def toggle_color_panel(self):
        if not self.color_panel:
            self.color_panel = ColorSelectionPanel(self)
            self.color_panel.set_parent_overlay(self)
        
        if self.color_panel.isVisible():
            self.color_panel.hide()
        else:
            menu_pos = self.mapToGlobal(self.rect().bottomRight())
            self.color_panel.move(menu_pos.x() + 10, menu_pos.y() - self.color_panel.height())
            self.color_panel.show()
            self.color_panel.raise_()

    def toggle_fix_position(self):
        self.fixed = not self.fixed
        self.settings.setValue('fixed', self.fixed)
        self.update_cursor()

    def open_bandwidth_dialog(self):
        if not self.monitor:
            return
        current_limit = self.monitor.get_bandwidth_limit()
        dialog = BandwidthLimitDialog(current_limit, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_limit = dialog.get_limit()
            self.monitor.set_bandwidth_limit(new_limit)
    
    def reset_to_default(self):
        # Clear all stored settings to defaults and ensure they are written
        self.settings.clear()
        self.settings.sync()
        # Restart the application to apply defaults
        QtCore.QProcess.startDetached(sys.executable, sys.argv)
        QtWidgets.qApp.quit()

    def update_text(self, dl, ul, total, limit, fullscreen):
        if fullscreen:
            self.hide()
        else:
            self.show()
            self.ensure_topmost()
        
        dl_str = format_speed(dl, self.speed_unit)
        ul_str = format_speed(ul, self.speed_unit)
        today_total_str = format_data_size(total)
        limit_str = format_data_size(limit)
        is_over_limit = total >= limit
        
        if is_over_limit:
            # Show warning icon if over limit
            self.label.setText(
                f"\u26A0 \u2193 {dl_str}   \u2191 {ul_str}\n"
                f"Today: {today_total_str} / {limit_str}"
            )
        else:
            # Normal display without icon
            self.label.setText(
                f"\u2193 {dl_str}   \u2191 {ul_str}\n"
                f"Today: {today_total_str} / {limit_str}"
            )
        
        # Resize box to fit text content
        self.label.adjustSize()
        self.resize(self.label.size())
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.update_size_grip()
