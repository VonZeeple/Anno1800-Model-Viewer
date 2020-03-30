import math


def convert_normal(norm):
    n_1 = [n * 1. / 255 * 2 - 1 for n in norm]
    length = math.sqrt(sum([n ** 2 for n in n_1]))
    return [n/length for n in n_1]


class Mesh:
    """Contain a list of trigs """
    def __init__(self, trigs, groups=None, materials=None):
        self.trigs = trigs
        self.groups = groups
        self.materials = materials
        self.vertices = Mesh.v_from_t(self.trigs)

    @staticmethod
    def v_from_t(trigs):
        out = []
        for t in trigs:
            for v in t.vertices:
                out += v.pos
                out += convert_normal(v.norm)
                out += v.tex
        return out

    @staticmethod
    def from_rdm(data):
        trigs = []
        for t in data['triangles']:
            vertices = [Vertex(**data['vertices'][i]) for i in t]
            trigs.append(Trig(vertices))
        groups = data['groups']

        m = data['materials']
        return Mesh(trigs, groups=groups, materials=m)

    @staticmethod
    def gen_square(size_x, size_y):
        n = (128, 255, 128)
        v1 = Vertex(pos=(0, 0, 0), norm=n, tex=(0, 1))
        v2 = Vertex(pos=(size_x, 0, 0), norm=n, tex=(1, 1))
        v3 = Vertex(pos=(size_x, 0, size_y), norm=n, tex=(1, 0))
        v4 = Vertex(pos=(0, 0, size_y), norm=n, tex=(0, 0))
        mesh = Mesh([Trig([v3, v2, v1]), Trig([v4, v3, v1])],
                    groups=[{'n': 0, 'offset': 0, 'size': 6}],
                    materials=[{'name': 'decal'}])
        return mesh


class Vertex:
    def __init__(self, **kwarg):
        # TODO: set default value to None
        self.pos = kwarg.get('pos', (0, 0, 0))
        self.norm = kwarg.get('norm', (128, 255, 128))
        self.tex = kwarg.get('tex', (0, 0))


# Ordered list of vertices
class Trig:
    def __init__(self, vertices):
        self.vertices = vertices
