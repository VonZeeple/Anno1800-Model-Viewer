from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo
from mesh import Mesh
from asset import Asset
import numpy as np


class Renderer:
    def __init__(self, manager):
        self.asset_manager = manager
        self.textures = {}
        self.shaderProgram = None
        self.initialized = False

    def initialize(self):
        self.textures = {}

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_FRONT)
        glEnable(GL_LIGHTING)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glClearColor(0.5, 0.7, 1, 1)

        light_pos = [1, 2, 0]
        # light_dir = [0.0, -1.0, -1.0]
        light_color = [1, 1, 1]
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, light_pos)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_color)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_color)

        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

        self.load_textures()

        # Shader program to run on CPU
        vertexShader = shaders.compileShader("""
        #version 330
        layout (location=0) in vec3 position;
        layout (location=1) in vec2 texCoords;
        out vec2 theCoords;
        void main()
        {
            gl_Position = vec4(position, 1);
            theCoords = texCoords;
        }
        """, GL_VERTEX_SHADER)

        fragmentShader = shaders.compileShader("""
        #version 330
        uniform sampler2D texUnit;
        in vec2 theCoords;
        out vec4 outputColour;
        void main()
        {
            outputColour = texture(texUnit, theCoords);
        }
        """, GL_FRAGMENT_SHADER)
        self.shaderProgram = shaders.compileProgram(vertexShader, fragmentShader)
        self.initialized = True

    def load_textures(self):
        for k in self.asset_manager.textures.keys():
            dds_image = self.asset_manager.textures[k]
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, dds_image.width, dds_image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                         dds_image.data)
            glGenerateMipmap(GL_TEXTURE_2D)
            self.textures[k] = tex_id

    def render_asset(self, asset):
        for m in asset.models:
            model_name = m.filename
            transformer = m.transformers[0]
            if transformer:
                pos = transformer.position
                rot = transformer.rotation
                scale = transformer.scale
            else:
                pos = (0, 0, 0)
                rot = (0, 0, 0, 0)
                scale = 1
            glPushMatrix()
            glTranslatef(*pos)
            glScalef(scale, scale, scale)
            glRotatef(*rot)
            self.render_model(self.asset_manager.meshes[model_name], materials=m.materials)
            glPopMatrix()
        # Render the decal
        glColor3f(1.0, 1.0, 1.0)
        for decal in asset.decals:
            if not decal.is_terrain():
                continue
            extent = decal.get_extents()

            pos = (0, 0, 0)
            rot = (0, 0, 0, 0)
            scale = 1
            glPushMatrix()
            glTranslatef(-extent[0], 0, -extent[2])
            glScalef(scale, scale, scale)
            glTranslatef(*pos)
            glRotatef(rot[0]*90, rot[1]*90, rot[2]*90, rot[3]*90)
            decal_mesh = Mesh.gen_square(extent[0]*2, extent[2]*2)
            decal_materials = {'decal': list(decal.materials.values())[0]}
            self.render_model(decal_mesh, materials=decal_materials)
            glPopMatrix()

    def render_model(self, mesh, materials=None):
        if mesh is None:
            return
        color_group = True
        colors = [(1., 1., 1.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.), (1., 0., 1.), (1., 1., 0.), (0.0, 1., 1.)]
        glColor3f(1.0, 1.0, 1.0)
        vertex_data = mesh.vertices
        vertex_data = np.array(vertex_data, dtype=np.float32)
        vbo_data = vbo.VBO(np.array(vertex_data, dtype=np.float32))
        vbo_data.bind()
        # Tutorial fixed pipeline rendering
        # https://www.youtube.com/watch?v=sUJo9KXFzAM

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        for i, group in enumerate(mesh.groups):
            group_name = str(mesh.materials[group['n']]['name'])
            if materials and (group_name in materials):
                texture = materials[group_name].get_diff_texture()
            else:
                texture = None

            if texture and texture in self.textures:
                glBindTexture(GL_TEXTURE_2D, self.textures[texture])
            else:
                glDisable(GL_TEXTURE_2D)

            if color_group:
                glColor3f(*colors[group['n']])
            # TODO:check the size of a vertex
            offset = int(group['offset'])
            size = int(group['size'])
            glVertexPointer(3, GL_FLOAT, 32, vbo_data + offset*32)
            glNormalPointer(GL_FLOAT, 32, vbo_data + 12 + offset*32)
            glTexCoordPointer(2, GL_FLOAT, 32, vbo_data+24 + offset*32)
            glDrawArrays(GL_TRIANGLES, 0, int(size))

    def render(self, model, asset):
        if not self.initialized:
            self.initialize()
            return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.5, 0.7, 1, 1)
        glColor3f(1.0, 1.0, 1.0)

        if isinstance(model, Mesh):
            glDisable(GL_TEXTURE_2D)
            self.render_model(model)
        elif isinstance(asset, Asset):
            glEnable(GL_TEXTURE_2D)
            self.render_asset(asset)


