import math
from anno_rdm_converter import rdm as rdm_conv


def convert_normal(norm):
    n_1 = [n * 1. / 255 * 2 - 1 for n in norm]
    length = math.sqrt(sum([n ** 2 for n in n_1]))
    return [n / length for n in n_1]


class Mesh:
    """Contain a list of trigs """

    def __init__(self, vertices, indices, groups=None):
        self.vertices = vertices
        self.groups = groups
        self.indices = indices
        self.ordered_vertices = []

        #TODO, this should be done by the renderer
        for i in self.indices:
            vertex = self.vertices[i]
            self.ordered_vertices += vertex.pos[0:3]
            self.ordered_vertices += convert_normal(vertex.norm[0:3])
            self.ordered_vertices += vertex.tex[0:2]

    @staticmethod
    def from_rdm(data):
        meshes = data.main_record.get('mesh', [])

        def parse_mesh(mesh):
            indices = [rdm_conv.VertexIndex.decode(t).index for t in mesh['faces']]
            vertices = [Vertex.from_rdm(v) for v in mesh['vertices']]
            groups = [{'offset': g.offset, 'size': g.size, 'n': g.n} for g in mesh['groups'].values()]
            return Mesh(vertices, indices, groups=groups)

        return Mesh.merge_meshes([parse_mesh(m) for m in meshes])

    @staticmethod
    def merge_meshes(mesh_list):
        vertices = []
        indices = []
        groups = []
        for mesh in mesh_list:
            groups += [{'offset': g['offset'] + len(indices), 'size': g['size'], 'n': g['n']} for g in mesh.groups]
            indices += [i + len(vertices) for i in mesh.indices]
            vertices += mesh.vertices
        return Mesh(vertices, indices, groups=groups)


    @staticmethod
    def gen_square(size_x, size_y):
        n = (128, 255, 128)
        v1 = Vertex(pos=(0, 0, 0), norm=n, tex=(0, 1))
        v2 = Vertex(pos=(size_x, 0, 0), norm=n, tex=(1, 1))
        v3 = Vertex(pos=(size_x, 0, size_y), norm=n, tex=(1, 0))
        v4 = Vertex(pos=(0, 0, size_y), norm=n, tex=(0, 0))
        mesh = Mesh(
            vertices=[v1, v2, v3, v4],
            indices=[2, 1, 0, 3, 2, 0],
            groups=[{'n': 0, 'offset': 0, 'size': 6}])
        return mesh


class Vertex:
    def __init__(self, **kwarg):
        # TODO: set default value to None
        self.pos = kwarg.get('pos', (0, 0, 0))
        self.norm = kwarg.get('norm', (128, 255, 128))
        self.tex = kwarg.get('tex', (0, 0))

    @staticmethod
    def from_rdm(data):
        rdm_vertex = rdm_conv.Vertex.decode(data)
        return Vertex(pos=rdm_vertex['pos'], norm=rdm_vertex['norm'], tex=rdm_vertex['tex'])
