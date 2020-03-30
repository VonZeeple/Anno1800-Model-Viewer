class Asset:
    """An asset is a group of meshes, props and properties...parsed from a .cfg file"""

    def __init__(self):
        self.data = None

    @staticmethod
    def from_tree(root):
        asset = Asset()
        asset.data = root
        return asset

    def get_center(self):
        return (self.data.find('Center.' + s).text for s in ['x', 'y', 'z'])

    def get_mesh_center(self):
        return (self.data.find('MeshCenter.' + s).text for s in ['x', 'y', 'z'])

    def get_models(self):
        return [Model3D.from_tree(m) for m in self.data.findall('Models/Config')]

    def get_decals(self):
        return [Decal.from_tree(m) for m in self.data.findall('Decals/Config')]

    def get_meshes_to_load(self):
        return [model.get_filename() for model in self.get_models()]

    def get_textures_to_load(self):
        # intelligent use of xpath
        norm_tex = [el.text for el in self.data.findall('.//cModelNormalTex')]
        diff_tex = [el.text for el in self.data.findall('.//cModelDiffTex')]
        metal_tex = [el.text for el in self.data.findall('.//cModelMetallicTex')]
        return list(set(norm_tex + diff_tex + metal_tex))


class Material:
    def __init__(self):
        self.data = None

    @staticmethod
    def from_tree(tree):
        material = Material()
        material.data = tree
        return material

    def get_name(self):
        return self.data.find('.//Name').text

    def get_diff_texture(self):
        tex = self.data.find('.//cModelDiffTex')
        if tex is not None:
            return tex.text
        else:
            return None


def get_vector_from_tree(tree, name, n=3):
    indices = ['x', 'y', 'z', 'w']
    vector = []
    for i in range(n):
        data = tree.find('{0}.{1}'.format(name, indices[i]))
        if data is None:
            return None
        vector.append(float(data.text))
    return vector

class Transformer:
    def __init__(self):
        self.data = None

    @staticmethod
    def from_tree(tree):
        transformer = Transformer()
        transformer.data = tree
        return transformer

    def get_pos(self):
        vector = get_vector_from_tree(self.data, './/Position', n=3)
        if vector is not None:
            return vector
        else:
            return [0, 0, 0]

    def get_rot(self):
        vector = get_vector_from_tree(self.data, './/Rotation', n=4)
        if vector is not None:
            return vector
        else:
            return [0, 0, 0]

    def get_scale(self):
        return float(self.data.find('.//Scale').text)


class Model3D:
    def __init__(self):
        self.data = None

    @staticmethod
    def from_tree(tree):
        model = Model3D()
        model.data = tree
        return model

    def get_transformer(self):
        tree = self.data.find('Transformer')
        if tree:
            return Transformer.from_tree(self.data.find('Transformer'))
        else:
            return None

    def get_filename(self):
        return self.data.find('FileName').text

    def get_materials(self):
        materials = self.data.findall('Materials/Config')
        if materials:
            mat_list = {}
            for m in materials:
                mat = Material.from_tree(m)
                mat_list[mat.get_name()] = mat
            return mat_list
        else:
            return None


class Decal(Model3D):
    def __init__(self):
        super().__init__()

    @staticmethod
    def from_tree(tree):
        decal = Decal()
        decal.data = tree
        return decal

    def is_terrain(self):
        type_decal = self.data.find('Type')
        if type_decal is not None:
            return type_decal.text == 'Terrain'
        else:
            return False

    def get_extents(self):
        return [float(self.data.find('Extents.' + s).text) for s in ['x', 'y', 'z']]

    def get_filename(self):
        return None

