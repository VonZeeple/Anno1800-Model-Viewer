from dataclasses import dataclass
import xml.etree.ElementTree as eTree


def parse_color(data, name, n=3):
    axes = ('r', 'g', 'b', 'a')
    return tuple(float(data.find(name + '.' + axes[i]).text) for i in range(n))


def parse_vector(data, name, n=3):
    axes = ('x', 'y', 'z', 'w')
    return tuple(float(data.find(name + '.' + axes[i]).text) for i in range(n))


@dataclass
class Asset:
    """An asset is a group of meshes, props and properties...parsed from a .cfg file"""

    config_type = 'MAIN'

    data: eTree.ElementTree = None
    render_property_flag: int = 134348928
    center: tuple = (0, 0, 0)
    extent: tuple = (0, 0, 0)
    radius: float = 0
    mass: float = 1
    drag: float = 1
    mesh_center: tuple = (0, 0, 0)
    mesh_extent: tuple = (0, 0, 0)
    mesh_radius: float = 0
    models: tuple = ()
    decals: tuple = ()

    @staticmethod
    def from_tree(root):
        asset = Asset()
        asset.data = root
        asset.parse_header()
        asset.parse_models()
        asset.parse_decal()
        return asset

    def parse_header(self):
        self.render_property_flag = int(self.data.find('RenderPropertyFlags').text)
        self.center = parse_vector(self.data, 'Center')
        self.extent = parse_vector(self.data, 'Extent')
        self.radius = float(self.data.find('Radius').text)
        self.mass = float(self.data.find('Mass').text)
        self.drag = float(self.data.find('Drag').text)
        self.mesh_center = parse_vector(self.data, 'MeshCenter')
        self.mesh_center = parse_vector(self.data, 'MeshExtent')
        self.mesh_radius = float(self.data.find('MeshRadius').text)

    def parse_models(self):
        models = self.data.findall('Models/Config')
        self.models = tuple(Model3D.from_tree(t) for t in models)

    def parse_decal(self):
        decals = self.data.findall('Decals/Config')
        self.decals = tuple(Decal.from_tree(t) for t in decals)

    def get_meshes_to_load(self):
        return [model.filename for model in self.models]

    def get_textures_to_load(self):
        norm_tex = []
        diff_tex = [el.text for el in self.data.findall('.//cModelDiffTex')]
        metal_tex = []
        return list(set(norm_tex + diff_tex + metal_tex))


@dataclass
class Material:
    config_type = 'MATERIAL'

    name: str = None
    shader_id: int = 8
    vertex_format: str = None
    # More to parse
    diffuse_enabled: int = 0
    diffuse_texture: str = None
    normal_enabled: int = 0
    normal_texture: str = None
    diffuse_color: tuple = (0, 0, 0)

    # More to parse

    @staticmethod
    def from_tree(tree):
        material = Material(**{
            'name': tree.find('Name').text,
            'shader_id': int(tree.find('ShaderID').text),
            'vertex_format': tree.find('VertexFormat').text,
            'diffuse_enabled': int(tree.find('DIFFUSE_ENABLED').text),
            'diffuse_texture': tree.find('cModelDiffTex').text,
            'normal_enabled': int(tree.find('NORMAL_ENABLED').text),
            'normal_texture': tree.find('cModelNormalTex').text,
            'diffuse_color': parse_color(tree, 'cDiffuseColor')

        })
        return material


@dataclass()
class Transformer:
    config_type = 'ORIENTATION_TRANSFORM'
    conditions: int
    position: tuple
    rotation: tuple
    scale: float

    @staticmethod
    def from_tree(tree):
        transformer = Transformer(**{
            'conditions': int(tree.find('Conditions').text),
            'position': parse_vector(tree, 'Position'),
            'rotation': parse_vector(tree, 'Rotation', n=4),
            'scale': float(tree.find('Scale').text)
        })

        return transformer


@dataclass
class FileCFG:
    config_type = 'FILE'
    transformer: Transformer
    adapt_terrain_height: int
    name: str


@dataclass
class PropContainer:
    pass


@dataclass
class Particles:
    pass


@dataclass
class Sequences:
    pass


@dataclass
class Lights:
    pass


@dataclass
class Model3D:
    config_type = 'MODEL'

    filename: str = ''
    transformers: tuple = ()
    materials: tuple = ()
    name: str = ''
    animations: tuple = ()
    ignore_ruin_state: bool = True

    @staticmethod
    def from_tree(tree):
        model = Model3D()
        model.filename = tree.find('FileName').text
        transformers = tree.findall('Transformer/Config')
        model.transformers = tuple(Transformer.from_tree(t) for t in transformers)
        materials = tree.findall('Materials/Config')
        model.materials = tuple(Material.from_tree(t) for t in materials)

        return model


@dataclass
class Decal:
    config_type = 'DECAL'
    materials: tuple
    type: str
    name: str
    extents: tuple
    tex_coords: tuple

    # other stuff to parse

    @staticmethod
    def from_tree(tree):
        materials = tuple(Material.from_tree(t) for t in tree.findall('Materials/Config'))
        decal = Decal(**{
            'materials': materials,
            'type': tree.find('Type').text,
            'name': tree.find('Name').text,
            'extents': parse_vector(tree, 'Extents'),
            'tex_coords': parse_vector(tree, 'TexCoords', n=4)
        })
        return decal

    def is_terrain(self):
        return self.type == 'Terrain'

    def get_extents(self):
        return self.extents
