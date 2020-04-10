from asset import *
import xml.etree.ElementTree as eTree
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
        root = eTree.parse(f)
    asset = Asset.from_tree(root)
    assert asset.render_property_flag == 101010
    assert asset.center == (-0.172626, 3.366896, 0.053605)
    assert asset.extent == (4.910677, 5.226009, 3.886663)
    assert asset.radius == 8.156719

def test_asset_model_parsing():
    filename = 'simple_model.cfg'
    with open(filename, 'rb') as f:
        root = eTree.parse(f)
    asset = Asset.from_tree(root)


def test_asset_decal_parsing():
    filename = 'decal_only.cfg'
    with open(filename, 'rb') as f:
        root = eTree.parse(f)
    asset = Asset.from_tree(root)
    assert len(asset.decals) == 1

def test_asset_parsing_error():
    filename = 'header_missing.cfg'
    with open(filename, 'rb') as f:
        root = eTree.parse(f)

    with pytest.raises(Exception) as error:
        asset = Asset.from_tree(root)
    assert str(error.typename) == 'AttributeError'
