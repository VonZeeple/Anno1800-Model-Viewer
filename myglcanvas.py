import wx
from wx import glcanvas
from math import *
from OpenGL.GL import *


class myGLCanvas(glcanvas.GLCanvas):
    def __init__(self, *arg, **kwargs):
        attrib_list = (glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24)
        super().__init__(*arg, attribList=attrib_list, **kwargs)

        self.gl_context = glcanvas.GLContext(self)

        #self.cb = wx.CheckBox(self, label='test')

    def set_view(self, angle_x, angle_y, zoom, trans_x, trans_y):
        size_x, size_y = self.GetClientSize()
        glViewport(0, 0, size_x, size_y)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glScalef(-1, 1, 1)
        fov = 20
        f = 1
        loc_y = tan(radians(fov)) * f
        loc_x = loc_y / size_y * size_x
        glFrustum(-loc_x, loc_x, -loc_y, loc_y, f, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, zoom - 10)
        glTranslatef(trans_x, trans_y, 0)
        glRotatef(angle_y, 1.0, 0.0, 0.0)
        glRotatef(-angle_x, 0.0, 1.0, 0.0)

