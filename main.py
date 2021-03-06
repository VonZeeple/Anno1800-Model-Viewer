import wx
from gui import MainWindow
from asset_manager import AssetManager

if __name__ == '__main__':
    app = wx.App()
    model = AssetManager()
    root = MainWindow(model, None, title='Anno1800 Asset Viewer', size=(1000, 700))
    model.window = root
    app.MainLoop()
