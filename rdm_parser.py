from struct import unpack

class NotRDMError(Exception):
    pass


class IntegerArrayError(Exception):
    pass


class VertexSizeError(Exception):
    pass


def get_groups(*args):
    return {'n': args[2], 'offset': args[0], 'size': args[1]}


def parse_rdm(data):
    header_dict = parse_header(data)
    # TODO: handle several meshes?
    v = parse_vertices(data, header_dict['meshes'][0]['vertices_offset'])
    t = parse_triangles(data, header_dict['meshes'][0]['triangles_offset'])
    g = header_dict['meshes'][0]['groups']
    m = header_dict['materials']
    return {'vertices': v, 'triangles': t, 'groups': g, 'materials': m}


def parse_header(data):
    # Some strings and usefull offsets
    RDMtag, = unpack('3s', data[0:3])
    if RDMtag != b"RDM":
        raise NotRDMError

    data_dict = {}
    offsets, = unpack_int_array(data, 28)

    string_offsets = unpack_int_array(data, offsets[0])
    mesh_offsets = unpack_int_array(data, offsets[1])
    materials_offsets = unpack_int_array(data, offsets[2])

    # Strings extraction
    for i, s in enumerate(string_offsets):
        data_dict['strings_{:}'.format(i)] = [unpack_anno_str(data, i) for i in s if i != 0]

    # Mesh offsets
    if mesh_offsets:
        data_dict['meshes'] = [parse_mesh_header(data, indices) for indices in mesh_offsets]

    # Materials offsets
    if materials_offsets:
        materials = [parse_materials(data, indices) for indices in materials_offsets]
        data_dict['materials'] = materials

    return data_dict


def parse_materials(data, offset):
    mat_indices_1, = unpack_int_array(data, offset[0])
    material = unpack_material(data, mat_indices_1)
    return material


def unpack_material(data, indices):
    string1 = unpack_anno_str(data, indices[0])
    string2 = unpack_anno_str(data, indices[1])
    data = indices[2::]
    return {'name': string1, 'texture': string2, 'data': data}


def parse_mesh_header(data, mesh_offsets):
    data_dict = {}
    mesh_offset_1 = mesh_offsets[0]
    mesh_offset_2 = mesh_offsets[1]
    mesh_offset_3 = mesh_offsets[2]
    vertices_offset = mesh_offsets[3]
    triangles_offset = mesh_offsets[4]
    groups_offset = mesh_offsets[5]
    # 17 autres dont la plupart = 0

    data_dict['vertices_offset'] = vertices_offset
    data_dict['triangles_offset'] = triangles_offset

    # LOD stuff?
    offset_1, = unpack_int_array(data, mesh_offset_1)
    data_dict['lod_strings'] = [unpack_anno_str(data, i) for i in offset_1 if i != 0]

    # I dont know what this is for
    offset_2, = unpack_int_array(data, mesh_offset_2)
    data_dict['unknown_data'] = [unpack_int_array(data, i) for i in offset_2 if i != 0]

    # vertex groups
    groups_indices = unpack_int_array(data, groups_offset)
    groups = []
    for g in groups_indices:
        groups.append(get_groups(*g))

    data_dict['groups'] = groups
    return data_dict


def unpack_ints(data):
    n = len(data)
    if n % 4 != 0:
        raise IntegerArrayError
    return unpack(int(n / 4) * 'I', data)


def unpack_anno_str(data, pos):
    if pos >= 8:
        strLen, dummy = unpack('II', data[pos - 8:pos])
        string, = unpack(str(strLen) + 's', data[pos:pos + strLen])
        string = string.decode()
    else:
        string = None
    return string


def unpack_int_array(data, offset):
    if offset < 8:
        return None
    num, size = unpack('II', data[offset - 8:offset])
    return [unpack_ints(data[offset + i * size:offset + (i + 1) * size]) for i in range(num)]


def parse_vertices(data, offset):
    num, size = unpack('II', data[offset - 8: offset])
    vertices = []
    for i in range(num):
        data_v = data[offset + i * size:offset + (i + 1) * size]
        vertices.append(unpack_vertex(data_v))
    return vertices


def parse_triangles(data, offset):
    num, size = unpack('II', data[offset - 8: offset])
    triangles = []
    for i in range(int(num / 3)):
        data_t = data[offset + i * 3 * size:offset + (i + 1) * 3 * size]
        triangles.append(unpack_triangle(data_t))
    return triangles


vertex_formats = {8: r'P4h',
                  16: r'P4h_T2h_C4c',
                  20: r'P4h_N4b_T2h_I4b',
                  24: r'P4h_N4b_G4b_B4b_T2h',
                  28: r'P4h_N4b_G4b_B4b_T2h_I4b',
                  32: r'P4h_N4b_G4b_B4b_T2h_C4b_C4b',
                  56: r'P4h_N4b_G4b_B4b_T2h_I4b_I4b_I4b_I4b_W4b_W4b_W4b_W4b',
                  # 60: r'P3f_N3b_37_T2f',
                  # 64: r'P3f_N3b_41_T2f',
                  # 68: r'P3f_N3b_45_T2f',
                  # 72: r'P3f_N3b_49_T2f',
                  }

data_size = {'e': 2, 'f': 4, 'b': 1, 'B': 1, 'c': 1}


def unpack_vertex(data):
    v_size = len(data)
    if v_size not in vertex_formats.keys():
        raise VertexSizeError

    format_str = vertex_formats[v_size]
    vertex_arg = {'vformat': format_str}
    i = 0
    for s in format_str.replace('h', 'e').replace('b', 'B').split('_'):
        # TODO: implement regex for >56 bytes vertex
        num_data = int(s[1])
        if s[0] == 'P':
            vertex_arg['pos'] = unpack('3' + s[2], data[i:i + 3 * data_size[s[2]]])
        if s[0] == 'T':
            vertex_arg['tex'] = unpack('2' + s[2], data[i:i + 2 * data_size[s[2]]])
        if s[0] == 'N':
            vertex_arg['norm'] = unpack('3' + s[2], data[i:i + 3 * data_size[s[2]]])
        i += num_data * data_size[s[2]]
    if len(data) > 19:
        vertex_arg['material'], = unpack('B', data[15:16])
    return vertex_arg


class TriangleSizeError(Exception):
    pass


triangle_formats = {2: r'HHH',
                    4: r'III',
                    }


def unpack_triangle(data):
    t_size = int(len(data) / 3)
    if t_size not in triangle_formats.keys():
        raise TriangleSizeError
    i1, i2, i3 = unpack(triangle_formats[t_size], data)
    return [i1, i2, i3]
