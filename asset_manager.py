import rdm_parser
from PIL import Image
from mesh import Mesh
from asset import Asset, PRP
import os
import lxml.etree as etree


def open_file(file_path):
    with open(file_path, 'rb') as f:
        return f.read()

class AssetManager:
    def __init__(self):
        self.data_path = 'D:\\modding\\Anno1800\\data_Anno1800\\'
        self.window = None
        self.file_path = ''
        self.main_rdm_model = Mesh.gen_square(1, 1)
        self.main_asset = None

        # a dictionnary of all the meshes (rdm files). keys are the mesh relative path+filename
        self.meshes = {}
        # a dictionnary of all the textures (dds). keys are the texture relative path+filename
        self.textures = {}
        # a dictionnary of all the su-assets (cfg files). keys are the cfg file relative path+filename
        self.sub_assets = {}
        # a dictionnary of all the props (prp files). keys are the cfg file relative path+filename
        self.props = {}

    def delete_data(self):
        self.main_rdm_model = None
        self.main_asset = None
        self.meshes = {}
        self.textures = {}
        self.sub_assets = {}
        self.props = {}

    #  File loading and parsing
    def after_loading(self):
        if self.window is not None:
            self.window.on_file_load()

    def set_data_path(self, path):
        self.data_path = path
        print("Data path:", path)

    def set_file_path(self, path):
        self.file_path = path

    def load_main_file(self):
        formats = ['.cfg', '.rdm']# We can only load cfg and rdm files atm
        filename = self.file_path
        _, ext = os.path.splitext(filename)
        if ext not in formats:
            print("Format not supported")
            return None
        self.delete_data()
        try:
            if ext == '.cfg':
                self.parse_main_cfg(filename)
            elif ext == '.rdm':
                self.parse_main_rdm(filename)
        except Exception as e:
            print(e)
        else:
            print("File loaded and parsed")
            self.after_loading()


    def parse_main_rdm(self, filename):
        data = open_file(filename)
        mesh = rdm_parser.parse_rdm(data)
        self.main_rdm_model = Mesh.from_rdm(mesh)

    def parse_main_cfg(self, filename):
        self.parse_cfg_file(filename, is_main=True)


    def parse_rdm_file(self, filename):
        if filename not in self.meshes.keys():
            data = open_file(self.data_path+filename)
            mod = rdm_parser.parse_rdm(data)
            self.meshes[filename] = Mesh.from_rdm(mod)

    def parse_prp_file(self, filename):
        if filename not in self.props.keys():
            parser = etree.XMLParser(recover=True)
            root = etree.parse(self.data_path+filename, parser=parser)
            prop = PRP.from_tree(root)
            self.props[filename] = prop
            if prop.mesh_filename not in self.meshes.keys():
                self.parse_rdm_file(prop.mesh_filename)
            textures = prop.get_textures_to_load()
            if textures:
                for tex in textures:
                    self.load_texture(tex)
        # Parse models and materials...

    # Recursive parsing
    def parse_cfg_file(self, filename, is_main=False):
        # We check if this cfg have already been parsed
        if filename in self.sub_assets.keys():
            return
        if is_main:
            root = etree.parse(filename)
        else:
            root = etree.parse(self.data_path+filename)

        asset = Asset.from_tree(root)
        if is_main:
            self.main_asset = asset
        self.sub_assets[filename] = asset
        # We first parse all cfg files
        for cfg in asset.files:
            self.parse_cfg_file(cfg.filename)
        # We now parse all prp files
        for prp in asset.get_props():
            self.parse_prp_file(prp.filename)
        # We now parse all models
        for rdm in asset.get_meshes_to_load():
            self.parse_rdm_file(rdm.filename)
        # We now parse all textures
        for tex in asset.get_textures_to_load():
            self.load_texture(tex)

    def load_texture(self, filename):
        if filename is None:
            return
        if filename in self.textures.keys():
            return
        prefix, ext = os.path.splitext(filename)
        if ext == '.dds':
            tex = self.load_dds(prefix+'_0.dds')
        elif ext == '.psd':
            # Maybe try to find psd file first
            tex = self.load_dds(prefix+'_0.dds')
        elif ext == '.png':
            # Maybe try to find psd file first
            tex = self.load_dds(prefix+'_0.dds')
        else:
            tex = None
            print("texture format not supported: "+filename)
        if tex:
            self.textures[filename] = tex

    def load_dds(self, file_path):
        path = self.data_path + file_path
        try:
            im = Image.open(path)
            converted = im.convert("RGBA")
            buffer = converted.tobytes()
            height = im.height
            width = im.width
            format = "RGBA"
            # len(self.buffer) / (image.width * image.height)
            im.close()
            dds_file = DDSImage(buffer, height, width, format)
        except:
            print("can't open ", path)
        else:
            return dds_file


class DDSImage:
    def __init__(self, data, height, width, format):
        self.data = data
        self.height = height
        self.width = width
        self.format = format