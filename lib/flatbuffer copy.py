import generated.glTF_generated as flat
import re

from flatbuffers import flexbuffers, Builder
from enum import Enum
import numpy as np

class AccessorType(Enum):
    SCALAR = 0
    VEC2 = 1
    VEC3 = 2
    VEC4 = 3
    MAT2 = 4
    MAT3 = 5
    MAT4 = 6
    
class AnimationChannelTargetPath(Enum):
    translation = 0
    rotation = 1
    scale = 2
    weights = 3
    

class CameraType(Enum):
    perspective = 0
    orthographic = 1
    

# str - Strings
# bytes - FlexBuffers
# int - Number
# dicts - Structs
gltf_schema = {
    "accessors": [{
        "bufferView": int,
        "byteOffset": int,
        "componentType": int,
        "normalized": bool,
        "count": int,
        "type": AccessorType,
        "max": [int],
        "min": [int],
        "sparse": {
            "count": int,
            "indices": {
                "bufferView": int,
                "byteOffset": int,
                "componentType": int,
                "extension": bytes,
                "extras": bytes,
            },
            "values": {
                "bufferView": int,
                "byteOffset": int,
                "extension": bytes,
                "extras": bytes,
            },
            "extension": bytes,
            "extras": bytes,
        },
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "animations": [{
        "channels": [{
            "sampler": int,
            "target": AnimationChannelTargetPath,
            "extensions": bytes,
            "extras": bytes
        }],
        "samplers": [{
            "input": int,
            "interpolation": str,
            "output": int,
            "extensions": bytes,
            "extras": bytes,
        }],
        "name": str,
        "extension": bytes,
        "extras": bytes,
    }],
    "asset": {
        "copyright": str,
        "generator": str,
        "version": str,
        "minVersion": str,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    },
    "buffers": [{
        "uri": str,
        "byteLength": int,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "bufferViews": [{
        "buffer": int,
        "byteOffset": int,
        "byteLength": int,
        "byteStride": int,
        "target": int,
        "name": str,
        "extensions": bytes,
        #"extras": bytes, # struct.error :\
    }],
    "cameras": [{
        "orthographic": {
            "xmag": float,
            "ymag": float,
            "zfar": float,
            "znear": float,
            "extensions": bytes,
            "extras": bytes,
        },
        "perspective": {
            "aspectRatio": float,
            "yfov": float,
            "zfar": float,
            "znear": float,
            "extensions": bytes,
            "extras": bytes,
        },
        "type": CameraType,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "extensions": bytes,
    "extras": bytes,
    "images": [{
        "uri": str,
        "mimeType": str,
        "bufferView": int,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "materials": [{
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "meshes": [{
        "primitives": [{
            "attributes": bytes,
            "indices": int,
            "material": int,
            "mode": int,
            "targets": [int],
            "extensions": bytes,
            "extras": bytes,
        }],
        "weights": [int],
        "name": str,
        "extensions": bytes,
        "extras": bytes
    }],
    "nodes": [{
        "camera": int,
        "children": [int],
        "skin": int,
        "matrix": [int],
        "mesh": int,
        "rotation": [int],
        "scale": [int],
        "translation": [int],
        "weights": [int],
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "samplers": [{
        "magFilter": int,
        "minFilter": int,
        "wrapS": int,
        "wrapT": int,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "scenes": [{
        "nodes":[int],
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "skins": [{
        "inverseBindMatrices": int,
        "skeleton": int,
        "joints": [int],
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "textures": [{
        "sampler": int,
        "source": int,
        "name": str,
        "extensions": bytes,
        "extras": bytes,
    }],
    "scene": int
}

#! ---------------- Deserializing ---------------- 

def pascal_case(value: str):
    """
    Converts glTF camel case variable names to Pascal Case like in Flatbuffer
    """
    return value[0].upper() + value[1:]

def preprocess_data(data: any):
    """
    The `preprocess_data` function takes in any data and applies specific preprocessing steps based on
    the data type.

    :param data: The parameter "data" can be of any type.
    :type data: any
    :return: Preprocessed data
    """
    if isinstance(data, list):
        if (len(data) == 0): return None
        return preprocess_list(data)
    elif isinstance(data, dict):
        if (len(data.keys()) == 0): return None
        return preprocess_dict(data)
    elif isinstance(data, float):
        return round(data, 6)
    elif isinstance(data, int):
        if (data == -1): 
            return None

    return data


def preprocess_list(data: list) -> list:
    """
    The function preprocess_list takes a list of data, removes any None values, and applies a
    preprocessing function to each remaining value before returning the processed list.

    :param data: The parameter `data` is a list of values that need to be preprocessed
    :type data: list
    :return: preprocessed list.
    """
    result = []

    for value in data:
        pre_value = preprocess_data(value)
        
        if pre_value is None:
            continue
        else:
            result.append(pre_value)

    return result


def preprocess_dict(data: dict) -> dict:
    """
    The function preprocesses a dictionary by removing any key-value pairs where the value is None and
    applying a preprocessing function to the remaining values.

    :param data: A dictionary containing key-value pairs
    :type data: dict
    :return: Preprocessed dictionary.
    """
    result = {}

    for key, value in data.items():
        pre_value = preprocess_data(value)

        if pre_value is None:
            continue
        else:
            result[key] = pre_value

    return result

def deserialize_string(data: bytes or None) -> str:
    if data is None:
        return None

    return data.decode("utf8")

def deserialize_flexbuffer(data: np.ndarray) -> any:
    if isinstance(data, int) and data == 0:
        return None

    data_array = bytearray(data)
    return flexbuffers.Loads(data_array)

#def deserialize_array(data: np.ndarray) -> list:
#    if isinstance(data, int) and data == 0:
#        return None
#    
#    return data.tolist()

def deserialize_array(buffer: any, key: str, schema: any) -> list:
    
    # List of numbers
    if (schema == int or schema == float):
        number_array = getattr(buffer, f"{key}AsNumpy")()
        if (isinstance(number_array, int) and number_array == 0): return None
        return number_array.tolist()
    
    # Structs
    elif (isinstance(schema, dict)):
        result = []
        object_number = getattr(buffer, f"{key}Length")()
        for i in range(object_number):
            object_buffer = getattr(buffer, key)(i)
            result.append(deserialize_flatbuffer(object_buffer, schema))
            
        return result
        

def deserialize_flatbuffer(buffer: any, schema: dict) -> dict:
    result = {}
    
    for key, value in schema.items():
        getter_key = pascal_case(key)
        
        # Numbers & Booleans | Simple Types
        if (value == int or value == bool or value == float):
            result[key] = getattr(buffer, getter_key)()
        
        # Strings
        elif (value == str):
            result[key] = deserialize_string(getattr(buffer, getter_key)())
            
        # FlexBuffers
        elif (value == bytes):
            result[key] = deserialize_flexbuffer(getattr(buffer, f"{getter_key}AsNumpy")())
        
        # Array Of Objects
        elif (isinstance(value, list)):
            result[key] = deserialize_array(buffer, getter_key, value[0])
        
        # Structs
        elif (isinstance(value, dict)):
            struct_buffer = getattr(buffer, getter_key)()
            if (struct_buffer == None): 
                continue

            result[key] = deserialize_flatbuffer(struct_buffer, schema[key])
            
        # String-Enum
        elif (issubclass(value, Enum)):
            enum_value = getattr(buffer, getter_key)()
            result[key] = value(enum_value).name

    
    return result

def deserialize_glb_json(data: bytes) -> dict:
    """
    The function takes bytes of glTF FLA2 chunk data and returns a dictionary
    containing the deserialized JSON data.

    :param data: A bytes that represents glTF FLA2 chunk data
    :type data: bytes
    :return: JSON data in python dict that can be used for serialization to usual json or using in python
    """
    flatbuffer = flat.Root.GetRootAs(bytearray(data))

    #json = {
    #    "buffers": [],
    #    "accessors": [],
    #    "animations": [],
    #    "cameras": [],
    #    "bufferViews": [],
    #    "extensionsRequired": [],
    #    "extensionsUsed": [],
    #    "images": [],
    #    "textures": [],
    #    "materials": [],
    #    "meshes": [],
    #    "skins": [],
    #    "nodes": [],
    #    "samplers": [],
    #    "scenes": [],
    #}
    
    json = deserialize_flatbuffer(flatbuffer, gltf_schema)

    # Buffers
    #for i in range(flatbuffer.BuffersLength()):
    #    buffer = flatbuffer.Buffers(i)
    #    buffer_dict = {
    #        "byteLength": buffer.ByteLength(),
    #        "uri": deserialize_string(buffer.Uri()),
    #        "name": deserialize_string(buffer.Name()),
    #        "extensions": deserialize_flexbuffer(buffer.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(buffer.ExtrasAsNumpy()),
    #    }
#
    #    json["buffers"].append(buffer_dict)

    # Accessors
    #for i in range(flatbuffer.AccessorsLength()):
    #    accessor = flatbuffer.Accessors(i)
#
    #    accessor_dict = {
    #        "bufferView": accessor.BufferView(),
    #        "byteOffset": accessor.ByteOffset(),
    #        "componentType": accessor.ComponentType(),
    #        "count": accessor.Count(),
    #        "name": deserialize_string(accessor.Name()),
    #        "max": deserialize_array(accessor.MaxAsNumpy()),
    #        "min": deserialize_array(accessor.MinAsNumpy()),
    #        "extensions": deserialize_flexbuffer(accessor.ExtensionsAsNumpy()),
    #        "normalized": accessor.Normalized(),
    #        "extras": deserialize_flexbuffer(accessor.ExtrasAsNumpy()),
    #        "type": AccessorType(accessor.Type()).name,
    #    }
    #    
    #    accessor_sparse = accessor.Sparse()
    #    if (accessor_sparse is not None):
    #        accessor_sparse_indices = accessor_sparse.Indices()
    #        accessor_sparse_values = accessor_sparse.Values()
    #        accessor_sparse_dict = {
    #            "count": accessor_sparse.Count(),
    #            "indices": {
    #                "bufferView": accessor_sparse_indices.BufferView(),
    #                "byteOffset": accessor_sparse_indices.ByteOffset(),
    #                "componentType": accessor_sparse_indices.ComponentType(),
    #                "extensions": deserialize_flexbuffer(accessor_sparse_indices.ExtensionsAsNumpy()),
    #                "extras": deserialize_flexbuffer(accessor_sparse_indices.ExtrasAsNumpy()),
    #            },
    #            "values": {
    #                "bufferView": accessor_sparse_values.BufferView(),
    #                "byteOffset": accessor_sparse_values.ByteOffset(),
    #                "extensions": deserialize_flexbuffer(accessor_sparse_values.ExtensionsAsNumpy()),
    #                "extras": deserialize_flexbuffer(accessor_sparse_values.ExtrasAsNumpy()),
    #            },
    #            "extensions": deserialize_flexbuffer(accessor_sparse.ExtensionsAsNumpy()),
    #            "extras": deserialize_flexbuffer(accessor_sparse.ExtrasAsNumpy()),
    #        }
    #        
    #        accessor_dict["sparse"] = accessor_sparse_dict
#
    #    json["accessors"].append(accessor_dict)

    # Animations
    #for i in range(flatbuffer.AnimationsLength()):
    #    animation = flatbuffer.Animations(i)
    #    animation_channels_dict = []
    #    animation_samplers_dict = []
    #    
    #    # Animation Channels
    #    for t in range(animation.ChannelsLength()):
    #        animation_channel = animation.Channels(t)
    #        animation_channel_target = animation_channel.Target()
    #        animation_channel_dict = {
    #            "sampler": animation_channel.Sampler(),
    #            "target": {
    #                "node": animation_channel_target.Node(),
    #                "path": AnimationChannelTargetPath(animation_channel_target.Path()).name,
    #                "extensions": deserialize_flexbuffer(animation_channel_target.ExtensionsAsNumpy()),
    #                "extras": deserialize_flexbuffer(animation_channel_target.ExtrasAsNumpy())
    #            }
    #        }
#
    #        animation_channels_dict.append(animation_channel_dict)
#
    #    animation_dict = {
    #        "channels": animation_channels_dict,
    #        "samplers": animation_samplers_dict,
    #        "name": deserialize_string(animation.Name),
    #        "extensions": deserialize_flexbuffer(animation.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(animation.ExtrasAsNumpy())
    #    }
    #    
    #    json["animations"].append(animation_dict)
    
    # Cameras
    #for i in range(flatbuffer.CamerasLength()):
    #    camera = flatbuffer.Cameras(i)
    #    camera_dict = {
    #        "type": CameraType(camera.Type()).name,
    #        "name": deserialize_string(camera.Name()),
    #    }
    #    
    #    camera_perspective = camera.Perspective()
    #    camera_orthographic = camera.Orthographic()
    #    
    #    if (camera_perspective is not None):
    #        camera_dict["perspective"] = {
    #            "aspectRatio": camera_perspective.AspectRatio(),
    #            "yfov": camera_perspective.Yfov(),
    #            "zfar": camera_perspective.Zfar(),
    #            "znear": camera_perspective.Znear(),
    #            "extensions": deserialize_flexbuffer(camera_perspective.ExtensionsAsNumpy()),
    #            "extras": deserialize_flexbuffer(camera_perspective.ExtrasAsNumpy()),
    #        }
    #        
    #    if (camera_orthographic is not None):
    #        camera_dict["orthographic"] = {
    #            "xmag": camera_orthographic.Xmag(),
    #            "ymag": camera_orthographic.Ymag(),
    #            "zfar": camera_orthographic.Zfar(),
    #            "znear": camera_orthographic.Znear(),
    #            "extensions": deserialize_flexbuffer(camera_orthographic.ExtensionsAsNumpy()),
    #            "extras": deserialize_flexbuffer(camera_orthographic.ExtrasAsNumpy()),
    #        }
    #        
    #    json["cameras"].append(camera_dict)
    
    # Assets
    #asset = flatbuffer.Asset()
    #if (asset is not None):
    #    json["asset"] = {
    #        "name": deserialize_string(asset.Name()),
    #        "generator": deserialize_string(asset.Generator()),
    #        "minVersion": deserialize_string(asset.MinVersion()),
    #        "version": deserialize_string(asset.Version()),
    #        "copyright": deserialize_string(asset.Copyright()),
    #        "extensions": deserialize_flexbuffer(asset.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(asset.ExtrasAsNumpy()),
    #    }
    
    # BufferViews
    #for i in range(flatbuffer.BufferViewsLength()):
    #    buffer_view = flatbuffer.BufferViews(i)
    #    buffer_view_dict = {
    #        "buffer": buffer_view.Buffer(),
    #        "byteOffset": buffer_view.ByteOffset(),
    #        "byteLength": buffer_view.ByteLength(),
    #        "byteStride": buffer_view.ByteStride(),
    #        "target": buffer_view.Target(),
    #        "name": buffer_view.Name(),
    #        "extensions": deserialize_flexbuffer(buffer_view.ExtensionsAsNumpy()),
    #        #"extras": deserialize_flexbuffer(buffer_view.ExtrasAsNumpy()), # struct.error :\
    #    }
    #    
    #    json["bufferViews"].append(buffer_view_dict)
    
    # ExtensionsRequired
    #for i in range(flatbuffer.ExtensionsRequiredLength()):
    #    json["extensionsRequired"].append(
    #        deserialize_string(flatbuffer.ExtensionsRequired(i))
    #    )
        
    # ExtensionsUsed
    #for i in range(flatbuffer.ExtensionsUsedLength()):
    #    json["extensionsUsed"].append(
    #        deserialize_string(flatbuffer.ExtensionsUsed(i))
    #    )
    
    # Images
    #for i in range(flatbuffer.ImagesLength()):
    #    image = flatbuffer.Images(i)
    #    image_dict = {
    #        "name": deserialize_string(image.Name()),
    #        "mimeType": deserialize_string(image.MimeType()),
    #        "bufferView": image.BufferView(),
    #        "extensions": deserialize_flexbuffer(image.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(image.ExtrasAsNumpy()),
    #        "uri": deserialize_string(image.Uri())
    #    }
    #    
    #    json["images"].append(image_dict)
    
    # Materials
    #for i in range(flatbuffer.MaterialsLength()):
    #    material = flatbuffer.Materials(i)
    #    material_dict = {
    #        "extensions": deserialize_flexbuffer(material.ExtensionsAsNumpy())
    #    }
#
    #    json["materials"].append(material_dict)

    # Meshes
    #for i in range(flatbuffer.MeshesLength()):
    #    mesh = flatbuffer.Meshes(i)
    #    
    #    mesh_primitives_dict = []
    #    for t in range(mesh.PrimitivesLength()):
    #        mesh_primitive = mesh.Primitives(t)
    #        mesh_primitives_dict.append({
    #            "attributes": deserialize_flexbuffer(mesh_primitive.AttributesAsNumpy()),
    #            "mode": mesh_primitive.Mode(),
    #            "targets": deserialize_flexbuffer(mesh_primitive.TargetsAsNumpy()),
    #            "indices": mesh_primitive.Indices(),
    #            "material": mesh_primitive.Material(),
    #            "extensions": deserialize_flexbuffer(mesh_primitive.ExtensionsAsNumpy()),
    #            "extras": deserialize_flexbuffer(mesh_primitive.ExtrasAsNumpy())
    #        })
    #    
    #    mesh_dict = {
    #        "name": deserialize_string(mesh.Name()),
    #        "primitives": mesh_primitives_dict,
    #        "weights": deserialize_array(mesh.WeightsAsNumpy()),
    #        "extensions": deserialize_flexbuffer(mesh.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(mesh.ExtrasAsNumpy()),
    #    }
    #    
    #    json["meshes"].append(mesh_dict)

    # Skins
    #for i in range(flatbuffer.SkinsLength()):
    #    skin = flatbuffer.Skins(i)
    #    skin_dict = {
    #        "name": deserialize_string(skin.Name()),
    #        "skeleton": skin.Skeleton(),
    #        "inverseBindMatrices": skin.InverseBindMatrices(),
    #        "joints": deserialize_array(skin.JointsAsNumpy()),
    #        "extensions": deserialize_flexbuffer(skin.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(skin.ExtrasAsNumpy())
    #    }
    #    
    #    json["skins"].append(skin_dict)
    
    # Nodes
    #for i in range(flatbuffer.NodesLength()):
    #    node = flatbuffer.Nodes(i)
    #    node_dict = {
    #        "camera": node.Camera(),
    #        "children": deserialize_array(node.ChildrenAsNumpy()),
    #        "weights": deserialize_array(node.WeightsAsNumpy()),
    #        "matrix": deserialize_array(node.MatrixAsNumpy()),
    #        "mesh":  node.Mesh(),
    #        "name": deserialize_string(node.Name()),
    #        "rotation": deserialize_array(node.RotationAsNumpy()),
    #        "scale": deserialize_array(node.ScaleAsNumpy()),
    #        "skin": node.Skin(),
    #        "translation": deserialize_array(node.TranslationAsNumpy()),
    #        "matrix": deserialize_array(node.MatrixAsNumpy())
    #    }
    #    
    #    json["nodes"].append(node_dict)
    
    # Samplers
    #for i in range(flatbuffer.SamplersLength()):
    #    sampler = flatbuffer.Samplers(i)
    #    sampler_dict = {
    #        "wrapS": sampler.WrapS(),
    #        "wrapT": sampler.WrapT(),
    #        "magFilter": sampler.MagFilter(),
    #        "minFilter": sampler.MinFilter(),
    #        "name": deserialize_string(sampler.Name()),
    #        "extension": deserialize_flexbuffer(sampler.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(sampler.ExtrasAsNumpy()),
    #    }
    #    
    #    json["samplers"].append(sampler_dict)
    
    # Scenes
    #json["scene"] = flatbuffer.Scene()
    #for i in range(flatbuffer.ScenesLength()):
    #    scene = flatbuffer.Scenes(i)
    #    scene_dict = {
    #        "extensions": deserialize_flexbuffer(scene.ExtensionsAsNumpy()),
    #        "extras": deserialize_flexbuffer(scene.ExtrasAsNumpy()),
    #        "name": deserialize_string(scene.Name()),
    #        "nodes": deserialize_array(scene.NodesAsNumpy()),
    #    }
    #    
    #    json["scenes"].append(scene_dict)
    
    return preprocess_data(json)

#! ---------------- Serializing ---------------- 

def serialize_gather(builder: Builder, cls: any, gather: dict) -> any:
    """
    A place where dark magic happens.
    Serializes a dictionary `gather` into a flatbuffer using the
    provided `Builder` and class.
    
    :param builder: File builder
    :type builder: Builder
    :param cls: The `cls` parameter is the class object that we want to serialize. It is of type `any`,
    which means it can be any class object
    :type cls: any
    :param gather: The `gather` parameter is a dictionary that contains gathered data to be serialized. The
    keys of the dictionary represent the fields or attributes of the object, and the values represent
    the corresponding values of those fields
    :type gather: dict
    :return: the result of calling the `EndObject` function on the `builder` object.
    """
    class_name = cls.__name__
    start_function = getattr(flat, f"{class_name}Start")
    end_function = getattr(flat, f"{class_name}End")
    
    start_function(builder)
    for key, value in gather.items():
        add_function = getattr(flat, f"{class_name}Add{key}")
        add_function(builder, value)
    
    return end_function(builder)

def serialize_accessors(builder: Builder, data: dict or None) -> any:
    data_gather = {}
    
    return serialize_gather(builder, flat.Accessor, data_gather)

def serialize_animation(builder: Builder, data: dict or None) -> any:
    data_gather = {}
    
    return serialize_gather(builder, flat.Animation, data_gather)

def serialize_asset(builder: Builder, data: dict or None) -> any:
    data_gather = {}
    
    name = data.get("name")
    extensions = data.get("extensions")
    extras = data.get("extras")
    generator = data.get("generator")
    min_version = data.get("minVersion")
    version = data.get("version")
    copyright = data.get("copyright")

    if (name is not None):
        data_gather["Name"] = builder.CreateString(name)
        
    if (extensions is not None):
        data_gather["Extensions"] = builder.CreateByteVector(flexbuffers.Dumps(extensions))
        
    if (extras is not None):
        data_gather["Extras"] = builder.CreateByteVector(flexbuffers.Dumps(extras))
        
    if (generator is not None):
        data_gather["Generator"] = builder.CreateString(generator)
        
    if (min_version is not None):
        data_gather["MinVersion"] = builder.CreateString(min_version)
    
    if (version is not None):
        data_gather["Version"] = builder.CreateString(version)
        
    if (copyright is not None):
        data_gather["Copyright"] = builder.CreateString(copyright)
        
    return serialize_gather(builder, flat.Asset, data_gather)

def serialize_glb_json(data: dict) -> bytes:
    buffers_data = data.get("buffers")
    accessors_data = data.get("accessors")
    animations_data = data.get("animations")
    cameras_data = data.get("cameras")
    buffer_views_data = data.get("bufferViews")
    extensions_required_data = data.get("extensionsRequired")
    extensions_used_data = data.get("extensionsUsed")
    images_data = data.get("images")
    textures_data = data.get("textures")
    materials_data = data.get("materials")
    meshes_data = data.get("meshes")
    skins_data = data.get("skins")
    nodes_data = data.get("nodes")
    samplers_data = data.get("samplers")
    scenes_data = data.get("scenes")
    scene_data = data.get("scene")
    asset_data = data.get("asset")
    
    flatbuffer = Builder()
    
    asset = serialize_asset(flatbuffer, asset_data)
    
    # Root
    flat.RootStart(flatbuffer)
    flat.RootAddAsset(flatbuffer, asset)
    root = flat.RootEnd(flatbuffer)

    flatbuffer.Finish(root)
    return bytes(flatbuffer.Output())
    