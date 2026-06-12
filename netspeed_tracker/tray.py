import pystray, threading
from PIL import Image, ImageDraw

def create_image():
    img = Image.new('RGB', (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill="black")
    return img

def start_tray(app):
    def on_quit(icon, item):
        icon.stop()
        app.quit()

    icon = pystray.Icon("netspeed", create_image(), menu=pystray.Menu(
        pystray.MenuItem('Quit', on_quit)))
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
