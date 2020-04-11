from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo
from mesh import Mesh
from asset import Asset, TransformerOrientation
import numpy as np
import math

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
        # Render the models:
        for m in asset.models:
            model_name = m.filename

            glPushMatrix()
            for t in m.transformers:
                transformers = Renderer.get_chained_transformers(asset, t)
                Renderer.apply_transformers(transformers)
            self.render_model(self.asset_manager.meshes[model_name], materials=m.materials)
            glPopMatrix()

        # Render the files:
        for f in asset.files:
            a = self.asset_manager.sub_assets.get(f.filename, None)
            if a:
                self.render_asset(a)
        # Render the props:
        for pc in asset.prop_containers:
            for t in pc.transformers:
                transformers = Renderer.get_chained_transformers(asset, t)
                Renderer.apply_transformers(transformers)
            for p in pc.props:
                self.render_prop(p)
        # Render the decal
        glColor3f(1.0, 1.0, 1.0)
        for decal in asset.decals:
            if not decal.is_terrain():
                continue
            extent = decal.get_extents()

            glPushMatrix()
            glTranslatef(-extent[0], 0, -extent[2])
            for t in decal.transformers:
                transformers = Renderer.get_chained_transformers(asset, t)
                Renderer.apply_transformers(transformers)
            decal_mesh = Mesh.gen_square(extent[0]*2, extent[2]*2)
            decal_materials = {'decal': list(decal.materials)[0]}
            self.render_model(decal_mesh, materials=decal_materials)
            glPopMatrix()

    @staticmethod
    def get_chained_transformers(asset, t):
        transformer_list = []
        if t is None:
            return []
        if t.config_type == 'ORIENTATION_TRANSFORM':
            transformer_list += [t]
        elif t.config_type == 'OBJECTLINK_TRANSFORM':
            id = t.model_id
            if len(asset.models) > id:
                t2 = asset.models[id].transformers
                for t3 in t2:
                    transformer_list += Renderer.get_chained_transformers(asset, t3)

        return transformer_list
    @staticmethod
    def apply_transformers(transformer_list):
        for t in transformer_list:
            if not isinstance(t, TransformerOrientation):
                continue
            pos = t.position
            rot = t.rotation
            scale = t.scale
            glTranslatef(*pos)
            glRotatef(*rot)
            glScalef(*([scale]*3))

    def render_prop(self, prop):
        if prop.filename not in self.asset_manager.props.keys():
            return
        prp = self.asset_manager.props.get(prop.filename)
        filename = prp.mesh_filename
        mesh = self.asset_manager.meshes.get(filename, None)
        if not mesh:
            return
        pos = prop.position
        rot = prop.rotation
        scale = prop.scale
        glPushMatrix()
        glTranslatef(*pos)
        glRotatef(*rot)
        glScalef(*scale)
        self.render_model(mesh)
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
                texture = materials[group_name].diffuse_texture
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


