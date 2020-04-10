import rdm_parser
from PIL import Image
from mesh import Mesh
from asset import Asset
import os
import xml.etree.ElementTree as eTree


class AssetManager:
    def __init__(self):
        self.data_path = 'D:\\modding\\Anno1800\\\data_Anno1800\\'
        self.window = None
        self.file_path = ''
        self.current_3Dmodel = Mesh.gen_square(1, 1)
        self.current_asset = None
        self.meshes = {}
        self.textures = {}

    #  File loading and parsing
    def on_file_load(self):
        if self.window is not None:
            self.window.on_file_load()

    def set_data_path(self, path):
        self.data_path = path
        print("Data path:", path)

    def set_file_path(self, path):
        self.file_path = path

    def load_file(self):
        self.current_asset = None
        self.current_3Dmodel = None
        self.meshes = {}
        self.textures = {}

        data = self.open_file(self.file_path)
        if isinstance(data, Asset):
            self.current_asset = data
        elif isinstance(data, Mesh):
            self.current_3Dmodel = data
        self.on_file_load()

    def open_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        formats = ['.cfg', '.rdm']
        if ext not in formats:
            print("Format not supported")
            return None

        try:
            with open(file_path, 'rb') as f:
                if ext == '.rdm':
                    return AssetManager.parse_rdm_file(f)

                elif ext == '.cfg':
                    data = self.parse_cfg_file(f)

        except FileNotFoundError:
            print("File not accessible")
            return None
        except Exception as e:
            print(e)
        else:
            print("File loaded and parsed")
            return data

    @staticmethod
    def parse_rdm_file(f):
        mod = rdm_parser.parse_rdm(f.read())
        return Mesh.from_rdm(mod)

    def parse_cfg_file(self, f):
        root = eTree.parse(f)
        asset = Asset.from_tree(root)

        for s in asset.get_meshes_to_load():
            self.meshes[s] = self.open_file(self.data_path+s)

        print(asset.get_textures_to_load())
        for tex in asset.get_textures_to_load():
            self.load_texture(tex)
        return asset

    def load_texture(self, filename):
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
            print("texture format not supported")
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