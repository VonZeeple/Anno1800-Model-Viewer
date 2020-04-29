from asset import *
from asset_manager import *
import lxml.etree as etree
import pytest


# Test about parsing .cfg files
def test_asset_field_mutability():
    asset = Asset()
    asset2 = Asset()
    old_flag = asset2.render_property_flag
    asset.render_property_flag = 2
    assert asset.render_property_flag == 2
    assert asset2.render_property_flag != 2
    assert asset2.render_property_flag == old_flag


def test_asset_header_parsing():
    filename = 'header_only.cfg'
    with open(filename, 'rb') as f:
        root = etree.parse(f)
    asset = Asset.from_tree(root)
    assert asset.render_property_flag == 101010
    assert asset.center == (-0.172626, 3.366896, 0.053605)
    assert asset.extent == (4.910677, 5.226009, 3.886663)
    assert asset.radius == 8.156719


@pytest.mark.parametrize("filename", [
    'simple_model.cfg',
    'workshop_03.cfg',
])
def test_asset_model_parsing(filename):
    # filename = 'simple_model.cfg'
    with open(filename, 'rb') as f:
        root = etree.parse(f)
    asset = Asset.from_tree(root)


def test_asset_decal_parsing():
    filename = 'decal_only.cfg'
    with open(filename, 'rb') as f:
        root = etree.parse(f)
    asset = Asset.from_tree(root)
    assert len(asset.decals) == 1


def test_asset_parsing_error():
    filename = 'header_missing.cfg'
    with open(filename, 'rb') as f:
        root = etree.parse(f)

    with pytest.raises(Exception) as error:
        asset = Asset.from_tree(root)
    assert str(error.typename) == 'AttributeError'

@pytest.mark.parametrize("filename", [
    r'../tests/workshop_03.cfg'
])
def test_asset_manager_load_asset(filename):
    manager = AssetManager()
    manager.parse_main_cfg(filename)
    assert True

@pytest.mark.parametrize("filename", [
    r'../tests/workshop_03.cfg',
     '../tests/chair_01.prp'
])
def test_xml_parsing(filename):
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()
    assert root


@pytest.mark.parametrize("filename, tag", [
    ('../tests/chair_01.prp', 'Materials'),
    ('../tests/white_wall_curved.prp', 'Material'),
    ('../tests/chair_01.prp', 'VertexFormat'),
    ('../tests/white_wall_curved.prp', 'VertexFormat'),
    ('../tests/chair_01.prp', 'Type'),
    ('../tests/white_wall_curved.prp', 'Type'),
])
def test_prp_first_level_tag_parsing(filename, tag):
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()
    child = root.find(tag)
    assert child is not None


@pytest.mark.parametrize("filename, tag,texture_name", [
    ('../tests/chair_01.prp', 'Materials/Material/cModelDiffTex', 'data/graphics/props/shared_textures/prop_atlas_4k_diff.psd'),
    ('../tests/white_wall_curved.prp', 'Material/cModelDiffTex', 'data/graphics/props/shared_textures/prop_atlas_4k_diff.psd')
])
def test_prp_diff_texture_parsing(filename, tag, texture_name):
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()
    child = root.find(tag)
    assert child is not None
    if child is not None:
        assert child.text == texture_name


# TODO: test rotations in dlc01\graphics\buildings\3rd_party\3rd_party_06_kontor_02\3rd_party_06_kontor_02.cfg