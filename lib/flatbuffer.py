import lib.generated.glTF_generated as flat
from flatbuffers import flexbuffers, Builder
from enum import IntEnum
import numpy as np
from collections import OrderedDict

class AccessorType(IntEnum):
    SCALAR = 0
    VEC2 = 1
    VEC3 = 2
    VEC4 = 3
    MAT2 = 4
    MAT3 = 5
    MAT4 = 6


class AnimationChannelTargetPath(IntEnum):
    translation = 0
    rotation = 1
    scale = 2
    weights = 3
    

class AnimationSamplerInterpolationAlgorithm(IntEnum):
    LINEAR = 0
    STEP = 1
    CATMULLROMSPLINE = 2
    CUBICSPLINE = 3

class CameraType(IntEnum):
    perspective = 0
    orthographic = 1


# str - Strings
# bytes - FlexBuffers
# int - Integer
# float - Numbers
# dicts - Structs
gltf_schema = {
    "_type": flat.Root,
    "accessors": [
        {
            "_type": flat.Accessor,
            "bufferView": int,
            "byteOffset": int,
            "componentType": int,
            "normalized": (bool, False),
            "count": int,
            "type": AccessorType,
            "max": [float],
            "min": [float],
            "sparse": {
                "_type": flat.AccessorSparse,
                "count": int,
                "indices": {
                    "_type": flat.AccessorSparseIndices,
                    "bufferView": int,
                    "byteOffset": int,
                    "componentType": int,
                    "extensions": bytes,
                    "extras": bytes,
                },
                "values": {
                    "_type": flat.AccessorSparseValues,
                    "bufferView": int,
                    "byteOffset": int,
                    "extensions": bytes,
                    "extras": bytes,
                },
                "extensions": bytes,
                "extras": bytes,
            },
            "name": str,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "animations": [
        {
            "_type": flat.Animation,
            "name": str,
            "channels": [{
                    "_type": flat.AnimationChannel,
                    "sampler": int,
                    "target": {
                        "_type": flat.AnimationChannelTarget,
                        "node": int,
                        "path": AnimationChannelTargetPath,
                        "extensions": bytes,
                        "extras": bytes,
                    },
                    "extensions": bytes,
                    "extras": bytes,
            }],
            "samplers": [{
                    "_type": flat.AnimationSampler,
                    "input": int,
                    "interpolation": (AnimationSamplerInterpolationAlgorithm, AnimationSamplerInterpolationAlgorithm.LINEAR),
                    "output": int,
                    "extensions": bytes,
                    "extras": bytes,
            }],

            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "asset": {
        "_type": flat.Asset,
        "name": str,
        "copyright": str,
        "generator": str,
        "version": str,
        "minVersion": str,
        "extensions": bytes,
        "extras": bytes,
    },
    "buffers": [
        {
            "_type": flat.Buffer,
            "name": str,
            "uri": str,
            "byteLength": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "bufferViews": [
        {
            "_type": flat.BufferView,
            "name": str,
            "buffer": int,
            "byteOffset": int,
            "byteLength": int,
            "byteStride": (int, 0),
            "target": (int, 34962),
            "extensions": bytes,
            # "extras": bytes, # struct.error :\
        }
    ],
    "extensionsRequired": [str],
    "extensionsUsed": [str],
    "cameras": [
        {
            "_type": flat.Camera,
            "name": str,
            "type": CameraType,
            "orthographic": {
                "_type": flat.CameraOrthographic,
                "xmag": float,
                "ymag": float,
                "zfar": float,
                "znear": float,
                "extensions": bytes,
                "extras": bytes,
            },
            "perspective": {
                "_type": flat.CameraPerspective,
                "aspectRatio": float,
                "yfov": float,
                "zfar": float,
                "znear": float,
                "extensions": bytes,
                "extras": bytes,
            },
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "extensions": bytes,
    "extras": bytes,
    "images": [
        {
            "_type": flat.Image,
            "name": str,
            "uri": str,
            "mimeType": str,
            "bufferView": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "materials": [
        {
            "_type": flat.Material,
            "name": str,
            #"alphaMode": int,
            #"alphaCutoff": float,
            #"doubleSided": bool,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "meshes": [
        {
            "_type": flat.Mesh,
            "name": str,
            "primitives": [
                {
                    "_type": flat.MeshPrimitive,
                    "attributes": bytes,
                    "indices": int,
                    "material": int,
                    "mode": int,
                    "targets": bytes,
                    "extensions": bytes,
                    "extras": bytes,
                }
            ],
            "weights": [float],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "nodes": [
        {
            "_type": flat.Node,
            "camera": int,
            "children": [int],
            "skin": int,
            "matrix": [float],
            "mesh": int,
            "rotation": [float],
            "scale": [float],
            "translation": [float],
            "weights": [float],
            "name": str,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "samplers": [
        {
            "_type": flat.Sampler,
            "name": str,
            "magFilter": int,
            "minFilter": int,
            "wrapS": (int, 10497),
            "wrapT": (int, 10497),
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "scenes": [
        {
            "_type": flat.Scene,
            "name": str,
            "nodes": [int],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "skins": [
        {
            "_type": flat.Skin,
            "name": str,
            "inverseBindMatrices": int,
            "skeleton": int,
            "joints": [int],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "textures": [
        {
            "_type": flat.Texture,
            "name": str,
            "sampler": int,
            "source": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "scene": int
}

#! ---------------- Deserializing ----------------


def pascal_case(value: str):
    """
    Converts glTF camel case variable names to Pascal Case like in Flatbuffer
    """
    return value[0].upper() + value[1:]


def preprocess_data(data: any, clean: bool = False) -> any:
    """
    The `preprocess_data` function takes in any data and applies specific preprocessing steps based on
    the data type.

    :param data: The parameter "data" can be of any type.
    :type data: any
    :return: Preprocessed data
    """
    if isinstance(data, list):
        if clean and len(data) == 0:
            return None
        return preprocess_list(data)
    elif isinstance(data, dict):
        if len(data.keys()) == 0:
            return None
        return preprocess_dict(data)
    elif isinstance(data, float):
        return round(data, 6)
    elif isinstance(data, int):
        if data == -1:
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
    result = OrderedDict()

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
    try:
        return flexbuffers.Loads(data_array)
    except:
        pass


def deserialize_array(buffer: any, key: str, schema: any) -> list:
    # List of numbers
    if schema == int or schema == float:
        number_array = getattr(buffer, f"{key}AsNumpy")()
        if isinstance(number_array, int) and number_array == 0:
            return None
        return number_array.tolist()

    # Structs | strings
    elif isinstance(schema, dict) or schema == str:
        object_number = getattr(buffer, f"{key}Length")()
        if (object_number == 0):
            return None

        result = []
        for i in range(object_number):
            object_buffer = getattr(buffer, key)(i)
            if (schema == str):
                result.append(bytes(object_buffer).decode('utf8'))
            else:
                result.append(deserialize_flatbuffer(object_buffer, schema))
            
        return result


def deserialize_flatbuffer(buffer: any, schema: dict, clean: bool = False) -> dict:
    result = OrderedDict()

    for key, value in schema.items():
        if (key.startswith("_")):
            continue
        
        getter_key = pascal_case(key)
        value_type = value
        default_value = None
        value_data = None

        if (isinstance(value_type, tuple)):
            value_type, default_value = value

        # Numbers & Booleans | Simple Types
        if value_type == int or value_type == bool or value_type == float:
            value_data = getattr(buffer, getter_key)()

        # Strings
        elif value_type == str:
            value_data = deserialize_string(getattr(buffer, getter_key)())

        # FlexBuffers
        elif value_type == bytes:
            value_data = deserialize_flexbuffer(
                getattr(buffer, f"{getter_key}AsNumpy")()
            )

        # Array Of Objects
        elif isinstance(value_type, list):
            value_data = deserialize_array(buffer, getter_key, value_type[0])

        # Structs
        elif isinstance(value_type, dict):
            struct_buffer = getattr(buffer, getter_key)()
            if struct_buffer == None:
                continue

            value_data = deserialize_flatbuffer(struct_buffer, schema[key])

        # String-Enum
        elif issubclass(value_type, IntEnum):
            enum_value = getattr(buffer, getter_key)()
            if (enum_value == default_value): continue
            value_data = value_type(enum_value).name
        
        if (clean and value_data is None):
            continue
        
        if (default_value != value_data):
            result[key] = value_data if value_data is not None else default_value

    return result


def deserialize_glb_json(data: bytes, clean: bool = False) -> dict:
    """
    The function takes bytes of glTF FLA2 chunk data and returns a dictionary
    containing the deserialized JSON data.

    :param data: A bytes that represents glTF FLA2 chunk data
    :param clean: Returns cleaned data without empty arrays and default values
    :type data: bytes
    :return: JSON data in python dict that can be used for serialization to usual json or using in python
    """
    flatbuffer = flat.Root.GetRootAs(bytearray(data))

    output = deserialize_flatbuffer(flatbuffer, gltf_schema, clean)
    asset_info = output.get("asset", {"version": "2.0"})
    asset_info["generator"] = "Supercell glTF Converter by DaniilSV"
    output["asset"] = asset_info

    return preprocess_data(output, clean)


#! ---------------- Serializing ----------------


def serialize_gather(builder: Builder, class_name: str, gather: dict) -> any:
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
    start_function = getattr(flat, f"{class_name}Start")
    end_function = getattr(flat, f"{class_name}End")

    start_function(builder)
    for key, value in reversed(gather.items()):
        add_function = getattr(flat, f"{class_name}Add{key}")
        add_function(builder, value)

    return end_function(builder)


def serialize_array(
    builder: Builder, data: list, schema: any, class_name: str, key: str
) -> int or list:
    if schema == int:
        array = np.array(data, dtype=np.int32)
        return builder.CreateNumpyVector(array)

    elif schema == float:
        array = np.array(data, dtype=np.float32)
        return builder.CreateNumpyVector(array)
    
    elif isinstance(schema, dict) or schema == str:
        objects = []

        for object in data:
            if (object is None): continue
            
            if (schema == str):
                objects.append(builder.CreateString(object))
            else:
                objects.append(serialize_flatbuffer(builder, object, schema))

        object_count = len(objects)
        if (object_count == 0): return 0
        vector_start = getattr(flat, f"{class_name}Start{key}Vector")
        vector_start(builder, object_count)
        
        for object in reversed(objects):
            builder.PrependUOffsetTRelative(object)

        return builder.EndVector()


def serialize_flatbuffer(builder: Builder, data: dict, schema: dict) -> any:
    gather = {}

    class_name = schema.get("_type").__name__
    for key, value in schema.items():
        if key.startswith("_"):
            continue

        key_getter = pascal_case(key)
        key_data = data.get(key)
        if key_data == None:
            continue
        
        value_type = value
        default_value = None
        if (isinstance(value, tuple)):
            value_type, default_value = value
            
        if (key_data == default_value):
            continue

        # Simple Types
        if value_type == int or value_type == float or value_type == bool:
            gather[key_getter] = key_data

        # Strings
        if value_type == str:
            gather[key_getter] = builder.CreateString(key_data)

        # FlexBuffers
        elif value_type == bytes:
            gather[key_getter] = builder.CreateByteVector(flexbuffers.Dumps(key_data))

        # Array Of Objects
        elif isinstance(value_type, list):
            gather[key_getter] = serialize_array(
                builder, key_data, schema[key][0], class_name, key_getter
            )

        # Structs
        elif isinstance(value_type, dict):
            gather[key_getter] = serialize_flatbuffer(builder, key_data, schema[key])
        
        # String-Enum
        elif issubclass(value_type, IntEnum):
            enum_data = getattr(value_type, key_data)
            if (enum_data == default_value): continue
            gather[key_getter] = enum_data.value

    return serialize_gather(builder, class_name, gather)


def serialize_glb_json(data: dict) -> bytes:
    flatbuffer = Builder()

    root = serialize_flatbuffer(flatbuffer, data, gltf_schema)

    flatbuffer.Finish(root)
    return bytes(flatbuffer.Output())
