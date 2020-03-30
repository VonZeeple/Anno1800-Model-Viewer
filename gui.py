import wx
from myglcanvas import myGLCanvas
from renderer import Renderer

class MouseEventHandler:
    def __init__(self, frame):
        self.frame = frame
        self.old_x = 0
        self.old_y = 0

    def on_mouse_motion(self, event):
        new_x, new_y = event.GetPosition()
        if event.Dragging():
            self.frame.OnDrag(new_x - self.old_x, new_y - self.old_y, strat=event.RightIsDown())
        self.old_x = new_x
        self.old_y = new_y

    def on_mouse_wheel(self, event):
        self.frame.OnScroll(event.GetWheelRotation())


class EventHandler:
    def __init__(self, frame):
        self.frame = frame

    def on_pressed_exit_button(self, event):
        self.frame.Close()

    def on_pressed_folder_button(self, event):
        title = "Select Data folder"
        dlg = wx.DirDialog(self.frame, title, style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.frame.manager.set_data_path(dlg.GetPath())
        dlg.Destroy()

    def on_tree_selected_file(self, event):
        filename = self.frame.get_selected_file()
        self.frame.manager.set_file_path(filename)
        self.frame.manager.load_file()
        print(filename)

    def on_pressed_load_button(self, event):
        title = "Choose a file:"
        dlg = wx.FileDialog(self.frame, title,
                            style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.frame.manager.set_file_path(dlg.GetPath())
            self.frame.manager.load_file()
        dlg.Destroy()


class main_window(wx.Frame):
    def __init__(self, manager, *args, **kwargs):
        super(main_window, self).__init__(*args, **kwargs)
        self.manager = manager
        self.splitter_window = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D)
        self.tree_panel = Tree_panel(self.splitter_window, wx.ID_ANY)
        self.gl_panel = GLPanel(self.splitter_window, wx.ID_ANY)
        self.splitter_window.SplitVertically(self.tree_panel, self.gl_panel, 300)
        self.text_ctr = wx.TextCtrl(self)
        self.text_logger = wx.TextCtrl(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctr, 0.5, wx.ALL | wx.EXPAND)
        self.sizer.Add(self.splitter_window, 10, wx.ALL | wx.EXPAND)
        self.sizer.Add(self.text_logger, 3, wx.ALL | wx.EXPAND)
        self.SetSizer(self.sizer)
        self.event_handler = EventHandler(self)
        self.init_frame()
        self.Show()

    def on_file_load(self):
        self.gl_panel.Refresh()
        self.gl_panel.renderer.initialize()

    def get_selected_file(self):
        return self.tree_panel.get_selected_file()

    def init_frame(self):
        menu_bar = wx.MenuBar()
        file_button = wx.Menu()
        about_button = wx.Menu()
        load_item = file_button.Append(0, 'Load file', 'Status bar message')
        folder_item = file_button.Append(0, 'Select Data folder', 'Status bar message')
        exit_item = file_button.Append(wx.ID_EXIT, 'Exit', 'Status bar message')

        menu_bar.Append(file_button, '&File')
        menu_bar.Append(about_button, '&About')

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.event_handler.on_pressed_exit_button, exit_item)
        self.Bind(wx.EVT_MENU, self.event_handler.on_pressed_load_button, load_item)
        self.Bind(wx.EVT_MENU, self.event_handler.on_pressed_folder_button, folder_item)
        self.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.event_handler.on_tree_selected_file, self.tree_panel.tree)


class Tree_panel(wx.Panel):
    def __init__(self, *arg, **kwargs):
        super(Tree_panel, self).__init__(*arg, **kwargs)
        self.tree = wx.GenericDirCtrl(self, size=(100, 200))
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.tree, -1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def get_selected_file(self):
        return self.tree.GetPath()


class GLPanel(wx.Panel):
    # Usefull links: https://wiki.wxpython.org/GLCanvas
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.canvas = myGLCanvas(self, id=wx.ID_ANY, size=(500, 500))

        #self.canvas.get_context()

        self.GLinitialized = False
        self.angle_x = 0
        self.angle_y = 0
        self.trans_x = 0
        self.trans_y = 0
        self.zoom = 0
        self.renderer = Renderer(self.TopLevelParent.manager)

        # Event handlers
        self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.canvas.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.canvas.Bind(wx.EVT_PAINT, self.processPaintEvent)
        # Mouse events
        self.mouse_handler = MouseEventHandler(self)
        self.canvas.Bind(wx.EVT_MOTION, self.mouse_handler.on_mouse_motion)
        self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.mouse_handler.on_mouse_wheel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, -1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def OnDrag(self, dx, dy, strat=False):
        if strat:
            self.trans_x += -dx*0.01
            self.trans_y += -dy*0.01
        else:
            self.angle_x += dx
            self.angle_y += dy
        self.Refresh(False)

    def OnScroll(self, rotation):
        self.zoom += rotation * 0.01
        self.Refresh(False)

    def processEraseBackgroundEvent(self, event):
        pass  # Do nothing, to avoid flashing on MSWin

    def processSizeEvent(self, event):
        size = self.canvas.GetClientSize()
        self.OnReshape(size.width, size.height)
        self.canvas.Refresh(False)
        event.Skip()

    def processPaintEvent(self, event):
        """Process the drawing event."""
        self.PrepareGL()
        self.OnDraw()
        event.Skip()

    def PrepareGL(self):
        self.canvas.SetCurrent(self.canvas.gl_context)
        # initialize OpenGL only if we need to
        if not self.GLinitialized:
            self.GLinitialized = True
            size = self.canvas.GetClientSize()

        self.canvas.set_view(self.angle_x, self.angle_y, self.zoom, self.trans_x, self.trans_y)



    def OnReshape(self, width, height):
        """Reshape the OpenGL viewport based on the dimensions of the window."""
        if self.GLinitialized:
            self.canvas.set_view(self.angle_x, self.angle_y, self.zoom, self.trans_x, self.trans_y)

    def OnDraw(self, *args, **kwargs):
        """Draw the window."""

        model = self.TopLevelParent.manager.current_3Dmodel
        asset = self.TopLevelParent.manager.current_asset

        self.renderer.render(model, asset)
        self.canvas.SwapBuffers()




