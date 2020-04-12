from dataclasses import dataclass
#import xml.etree.ElementTree as eTree
from lxml  import etree

def parse_color(data, tag, n=3, axes=('r', 'g', 'b', 'a')):
    return parse_vector(data, tag, n=n, axes=axes)

def parse_str(data, tag, default):
    string = data.find('tag')
    if string is not None:
        return string.text
    else:
        return default

def parse_int(data, tag, default):
    string = data.find('tag')
    if string is not None:
        return int(string.text)
    else:
        return default

def parse_vector(data, tag, n=3, axes=('x', 'y', 'z', 'w')):
    vector = []
    for i in range(n):
        element = data.find(tag + '.' + axes[i])
        if element is None:
            return None
        else:
            vector.append(float(element.text))
    return tuple(vector)


@dataclass
class Asset:
    """An asset is a group of meshes, props and properties...parsed from a .cfg file"""

    config_type = 'MAIN'

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
    files: tuple = ()
    lights: tuple = ()
    prop_containers: tuple = ()

    @staticmethod
    def from_tree(root):
        asset = Asset()
        asset.parse_header(root)
        asset.parse_models(root)
        asset.parse_decal(root)
        asset.parse_files(root)
        asset.parse_lights(root)
        asset.parse_props(root)
        return asset

    def parse_header(self, data):
        self.render_property_flag = int(data.find('RenderPropertyFlags').text)
        self.center = parse_vector(data, 'Center')
        self.extent = parse_vector(data, 'Extent')
        self.radius = float(data.find('Radius').text)
        self.mass = float(data.find('Mass').text)
        self.drag = float(data.find('Drag').text)
        self.mesh_center = parse_vector(data, 'MeshCenter')
        self.mesh_center = parse_vector(data, 'MeshExtent')
        self.mesh_radius = float(data.find('MeshRadius').text)

    def parse_files(self, data):
        files = data.findall('Files/Config')
        self.files = tuple(FileCFG.from_tree(f) for f in files)

    def parse_props(self, data):
        props = data.findall('PropContainers/Config')
        self.prop_containers = tuple(PropContainer.from_tree(p) for p in props)

    def parse_lights(self, data):
        lights = data.findall('Lights/Config')
        self.lights = tuple(Light.from_tree(f) for f in lights)

    def parse_models(self, data):
        models = data.findall('Models/Config')
        self.models = tuple(Model3D.from_tree(t) for t in models)

    def parse_decal(self, data):
        decals = data.findall('Decals/Config')
        self.decals = tuple(Decal.from_tree(t) for t in decals)

    def get_props(self):
        props = []
        for pc in self.prop_containers:
            for p in pc.props:
                props.append(p)
        return props

    def get_meshes_to_load(self):
        return self.models

    def get_textures_to_load(self):
        textures = []
        for model in self.models:
            for material in model.materials:
                textures.append(material.diffuse_texture)
        for decal in self.decals:
            for material in decal.materials:
                textures.append(material.diffuse_texture)
        return textures


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
            'name': parse_str(tree, 'Name', None),
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
    @staticmethod
    def from_tree(tree):
        config_type = tree.find('ConfigType').text
        if config_type == 'ORIENTATION_TRANSFORM':
            return TransformerOrientation.from_tree(tree)
        elif config_type == 'OBJECTLINK_TRANSFORM':
            return TransformerObjectLink.from_tree(tree)
        else:
            return None


@dataclass()
class TransformerOrientation:
    config_type = 'ORIENTATION_TRANSFORM'
    conditions: int
    position: tuple
    rotation: tuple
    scale: float

    @staticmethod
    def from_tree(tree):
        transformer = TransformerOrientation(**{
            'conditions': int(tree.find('Conditions').text),
            'position': parse_vector(tree, 'Position'),
            'rotation': parse_vector(tree, 'Rotation', n=4),
            'scale': float(tree.find('Scale').text)
        })

        return transformer


@dataclass()
class TransformerObjectLink:
    config_type = 'OBJECTLINK_TRANSFORM'
    conditions: int
    model_id: int

    @staticmethod
    def from_tree(tree):
        transformer = TransformerObjectLink(**{
            'conditions': int(tree.find('Conditions').text),
            'model_id': int(tree.find('ModelID').text)
        })
        return transformer


@dataclass
class FileCFG:
    config_type = 'FILE'
    transformers: tuple
    adapt_terrain_height: int
    filename: str
    name: str

    @staticmethod
    def from_tree(tree):
        transformers = tuple(Transformer.from_tree(t) for t in tree.findall('Transformer/Config'))
        return FileCFG(**{
            'transformers': transformers,
            'adapt_terrain_height': int(tree.find('AdaptTerrainHeight').text),
            'name': tree.find('Name').text,
            'filename': tree.find('FileName').text
        })


@dataclass()
class Prop:
    config_type = 'PROP'
    filename: str
    position: tuple
    rotation: tuple
    scale: tuple
    flags: int

    @staticmethod
    def from_tree(tree):
        return Prop(**{
            'filename': tree.find('FileName').text,
            'position': parse_vector(tree, 'Position'),
            'rotation': parse_vector(tree, 'Rotation', n=4),
            'scale': parse_vector(tree, 'Scale'),
            'flags': int(tree.find('Flags').text)
        })


@dataclass
class PropContainer:
    config_type = 'PROPCONTAINER'
    transformers: tuple
    name: str
    variation_enabled: int
    variation_probability: int
    props: tuple

    @staticmethod
    def from_tree(tree):
        transformers = tuple(Transformer.from_tree(t) for t in tree.findall('Transformer/Config'))
        props = tuple(Prop.from_tree(t) for t in tree.findall('Props/Config'))
        return PropContainer(**{
            'transformers': transformers,
            'name': tree.find('Name').text,
            'variation_enabled': int(tree.find('VariationEnabled').text),
            'variation_probability': int(tree.find('VariationProbability').text),
            'props': props
        })


@dataclass
class Particles:
    pass


@dataclass
class Sequences:
    pass


@dataclass
class Light:
    config_type = 'LIGHT'
    transformers: tuple
    type: int

    @staticmethod
    def from_tree(tree):
        return None


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
    transformers: tuple
    type: str
    name: str
    extents: tuple
    tex_coords: tuple

    # other stuff to parse

    @staticmethod
    def from_tree(tree):
        materials = tuple(Material.from_tree(t) for t in tree.findall('Materials/Config'))
        transformer = tuple(Transformer.from_tree(t) for t in tree.findall('Transformer/Config'))
        decal = Decal(**{
            'materials': materials,
            'transformers': transformer,
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


@dataclass()
class PRP:
    type_file = 'SimplePBR'
    vertex_format: str
    mesh_filename: str
    materials: tuple
    # More to parse
    @staticmethod
    def from_tree(tree):
        materials = tree.findall('//Material')
        parsed_materials = tuple(PRPMaterial.from_tree(t) for t in materials)
        return PRP(**{
            'vertex_format': tree.find('VertexFormat').text,
            'mesh_filename': tree.find('MeshFileName').text,
            'materials': parsed_materials
        })

    def get_textures_to_load(self):
        textures = []
        for material in self.materials:
            textures.append(material.diffuse_texture)
        return textures

@dataclass
class PRPMaterial:

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
        texture = tree.find('cModelDiffTex')
        if texture is None:
            texture = tree.find('cPropDiffuseTex')

        material = Material(**{
            'diffuse_enabled': parse_int(tree, 'DIFFUSE_ENABLED', None),
            'diffuse_texture': texture.text,
            'normal_enabled': parse_int(tree, 'NORMAL_ENABLED', None),
            'normal_texture': parse_str(tree, 'cModelNormalTex', None),
            'diffuse_color': parse_color(tree, 'cDiffuseColor')

        })
        return material
