import wx


from gui import main_window
# import pyglet #Don't forget to install pillow, so pyglet can import DDS files
from asset_manager import AssetManager

if __name__ == '__main__':
    app = wx.App()
    model = AssetManager()
    root = main_window(model, None, title='Anno1800 Asset Editor', size=(1000, 700))
    model.window = root
    app.MainLoop()
