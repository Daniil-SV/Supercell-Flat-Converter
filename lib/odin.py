from lib.glTF import glTF, glTF_Chunk
from binary_reader import BinaryReader
from lib.gltf_constants import DataType, ComponentType
from lib.odin_attribute import OdinAttribute
from lib.odin_constants import OdinAttributeFormat, OdinAttributeType
import numpy as np
import json

## Exclusive Accessor Component Types
# 1 - Float Vector 3
# 2 - Float Vector 4
# 3 - Matrix4x4
# Idk what sense of modifying component type
# Maybe it more like GPU hint or smth like this

class BufferView:
    def __init__(self) -> None:
        self.stride: int = None
        self.data: bytes = b''
        self.offset: int = None
        
    def serialize(self):
        return {
            "buffer": 0,
            "byteOffset": self.offset,
            "byteLength": len(self.data),
            "byteStride": self.stride
        }

class SupercellOdinGLTF:
    UsedExtensions = [
        #"KHR_mesh_quantization",
        #"KHR_texture_transform",
        "SC_shader"
    ]
    
    RequiredExtensions = [
        #"KHR_mesh_quantization"
    ]
    
    def __init__(self, gltf: glTF) -> None:
        self.gltf = gltf
        self.json = gltf.get_chunk("JSON").data
        if isinstance(self.json ,bytes):
            self.json = json.loads(self.json)
        self.buffers: list[BufferView] = []
        self.odin_buffer_index: int = -1
        
        binary = gltf.get_chunk("BIN").data
        self.produce_buffers(binary)
        
    def process(self) -> glTF:
        self.process_meshes_raw()
        self.process_accessors()
        self.process_skins()
        self.process_nodes()
        
        extensions_required: list[str] = self.json.get("extensionsRequired", [])
        extensions_used: list[str] = self.json.get("extensionsUsed", [])
        
        has_odin = False
        if "SC_odin_format" in extensions_required:
            extensions_required.remove("SC_odin_format")
            has_odin = True
        
        if "SC_odin_format" in extensions_used:
            extensions_used.remove("SC_odin_format")
            has_odin = True
        
        if (has_odin):
            self.initialize_odin()
            self.process_meshes()

        return self.save()
    
    def process_accessors(self) -> None:
        accessors: list[dict] = self.json.get("accessors", [])
        
        for accessor in accessors:
            component = accessor["componentType"]
            
            # Masking Supercell custom index to make it valid
            accessor["componentType"] = component & 0x0000FFFF
    
    def process_meshes_raw(self) -> None:
        meshes: list[dict] = self.json.get("meshes", [])

        for mesh in meshes:
            primitives: dict = mesh.get("primitives")
            if (primitives is None): continue

            empty_primitives: list[int] = []

            for i, primitive in enumerate(primitives):
                # Empty primitives in animations bugfix
                if "attributes" not in primitive and "extensions" not in primitive:
                    empty_primitives.append(i)

                # Targets type bugfix
                targets = primitive.get("targets")
                if (isinstance(targets, dict)):
                    primitive.pop("targets")

            if new_primitives := [
                primitive
                for i, primitive in enumerate(primitives)
                if i not in empty_primitives
            ]:
                mesh["primitives"] = new_primitives
            else:
                mesh.pop("primitives")


    def process_nodes(self) -> None:
        nodes: list[dict] = self.json.get("nodes", [])
        
        childrens: dict[int, list[int]] = {}
        def add_child(idx: int, parent_idx: int):
            if (parent_idx not in childrens): childrens[parent_idx] = []
            childrens[parent_idx].append(idx)
        
        for i, node in enumerate(nodes):
            extensions: dict = node.get("extensions", {})
            if "SC_odin_format" not in extensions: continue
            
            odin: dict = extensions.pop("SC_odin_format")
            parent = odin.get("parent")
            add_child(i, parent)
            
        for idx, children in childrens.items():
            nodes[idx]["children"] = children
            
    def process_skins(self) -> None:
        skins: list[dict] = self.json.get("skins", [])
        
        for skin in skins:
            extensions: dict = skin.get("extensions", {})
            if "SC_odin_format" not in extensions: continue
            
            extensions.pop("SC_odin_format")
            
    def process_meshes(self) -> None:
        meshes: list[dict] = self.json.get("meshes", [])
        
        for mesh in meshes:
            extensions: dict = mesh.get("extensions", {})
            if "SC_odin_format" in extensions: extensions.pop("SC_odin_format")
            
            primitives = mesh.get("primitives")
            if (primitives is None): continue
            
            for primitive in primitives:
                self.process_mesh_primitive(primitive)
            
    def process_mesh_primitive(self, primitive: dict) -> None:
        extensions: dict = primitive.get("extensions", {})
        if "SC_odin_format" not in extensions: return
        
        odin = extensions.pop("SC_odin_format")
        indices = primitive.get("indices")
        count = self.calculate_odin_positions_count(self.json["accessors"][indices])
        descriptors: list[dict] = odin["vertexDescriptors"]
        attributes = {}
        
        for descriptor in descriptors:
            self.process_odin_primitive_descriptor(descriptor, attributes, count)
        
        primitive["attributes"] = attributes
        
    def process_odin_primitive_descriptor(self, descriptor: dict, attributes: dict, positions_count: int):
        attribute_descriptor: list[OdinAttribute] = []
        attribute_buffers: list[np.array] = []
        attribute_accessors: list[np.array] = []
        
        offset = descriptor["offset"]
        stride = descriptor["stride"]
        
        for i, attribute in enumerate(descriptor["attributes"]):
            attribute_type_index = attribute["index"]
            attribute_format_index = attribute["format"]
            if (attribute_type_index not in list(OdinAttributeType)):
                print(f"Unknown attribute name \"{attribute.get('name')}\". Skip...")
                continue
            
            if (attribute_format_index not in list(OdinAttributeFormat)):
                print(f"Unknown format \"{attribute_format_index}\" in attribute \"{attribute.get('name')}\". Skip...")
                continue
            
            attribute_type = OdinAttributeType(attribute_type_index)
            attribute_format = OdinAttributeFormat(attribute_format_index)
            isInteger = attribute["interpretAsInteger"]
            attribute = OdinAttribute(
                attribute_type,
                attribute_format,
                attribute["offset"]
            )
            
            attribute_buffers.append(np.zeros((positions_count, attribute.elements_count), dtype=attribute.data_type))
            attribute_descriptor.append(attribute)
            attribute_accessors.append(
                {
                    "bufferView": len(self.buffers) + i,
                    "componentType": OdinAttributeFormat.to_accessor_component(attribute_format),
                    "normalized": isInteger == False,
                    "count": int(positions_count),
                    "type": OdinAttributeFormat.to_accessor_type(attribute_format)
                }
            )
        
        mesh_buffer = self.buffers[self.odin_buffer_index].data
        for tris_idx in range(positions_count):
            for attr_idx, attribute in enumerate(attribute_descriptor):
                value_offset = offset + (stride * tris_idx) + attribute.offset
                buffer = attribute_buffers[attr_idx]
                buffer[tris_idx] = attribute.read(mesh_buffer, value_offset)

        for i, attribute in enumerate(attribute_descriptor):
            attribute_name = OdinAttributeType.to_attribute_name(attribute.type)
            attributes[attribute_name] = len(self.json["accessors"]) + i
            
            buffer_view = BufferView()
            buffer_view.data = attribute_buffers[i].tobytes()
            self.buffers.append(buffer_view)

        self.json["accessors"].extend(attribute_accessors)
        
    def process_animation(self, animation: dict) -> None:
        animations = self.json.get("animations", [])
        
        frame_rate = animation["frameRate"]
        frame_spf = 1.0 / frame_rate
        keyframes_count = animation["keyframeCount"]
        used_nodes = animation["nodes"]
        odin_animation_accessor = animation["accessor"]

        animation_transform_array = self.decode_accessor_obj(self.json["accessors"][odin_animation_accessor])
                    # Position + Quaternion Rotation + Scale
        frame_transform_length = 3 + 4 + 3
        animation_transform_array = np.reshape(animation_transform_array, (len(used_nodes), keyframes_count, frame_transform_length))

        # Animation input
        animation_input_index = len(self.json["accessors"])
        animation_input_buffer = BinaryReader()
        for i in range(keyframes_count):
            animation_input_buffer.write_float(frame_spf * i)
        self.json["accessors"].append(
            {
                "bufferView": len(self.json["bufferViews"]),
                "componentType": 5126,
                "count": keyframes_count,
                "type": "SCALAR"
            }
        )
        buffer_view = BufferView()
        buffer_view.data = bytes(animation_input_buffer.buffer())
        self.buffers.append(buffer_view)
        
        # Animation Transform
        animation_buffers_indices: list[tuple[int, int, int]] = []
        animation_transform_buffers: list[list[BinaryReader, BinaryReader, BinaryReader]] = [[BinaryReader() for _ in range(3)] for _ in used_nodes]
        for node_index in range(len(used_nodes)):
            for frame_index in range(keyframes_count):
                #print(node_index)
                translation, rotation, scale = animation_transform_buffers[node_index]
                t, r, s = np.array_split(animation_transform_array[node_index][frame_index], [3, 7])
                
                for value in t:
                    translation.write_float(value)
                
                for value in r:
                    rotation.write_float(value)
                
                for value in s:
                    scale.write_float(value)

        for buffer in animation_transform_buffers:
            translation, rotation, scale = buffer
            base_accessor_index = len(self.json["accessors"])
            base_bufferView_index = len(self.buffers)
            
            # Translation
            self.json["accessors"].append(
                {
                    "bufferView": base_bufferView_index,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC3"
                }
            )
            translation_buffer_view = BufferView()
            translation_buffer_view.data = bytes(translation.buffer())
            self.buffers.append(translation_buffer_view)
            
            # Rotation
            self.json["accessors"].append(
                {
                    "bufferView": base_bufferView_index + 1,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC4"
                }
            )
            rotation_buffer_view = BufferView()
            rotation_buffer_view.data = bytes(rotation.buffer())
            self.buffers.append(rotation_buffer_view)
            
            # Scale
            self.json["accessors"].append(
                {
                    "bufferView": base_bufferView_index + 2,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC3"
                }
            )
            scale_buffer_view = BufferView()
            scale_buffer_view.data = bytes(scale.buffer())
            self.buffers.append(scale_buffer_view)
            
            animation_buffers_indices.append(
                [
                    base_accessor_index,
                    base_accessor_index + 1,
                    base_accessor_index + 2
                ]
            )
        
        # Animation channels
        animation_channels: list[dict] = []
        animation_samplers: list[dict] = []
        for node_number, node_index in enumerate(used_nodes):
            translation, rotation, scale = animation_buffers_indices[node_number]
            
            # Translation
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {
                        "node": node_index,
                        "path": "translation"
                    }
                }
            )
            animation_samplers.append(
                {
                    "input": animation_input_index,
                    "output": translation
                }
            )
            
            # Rotation
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {
                        "node": node_index,
                        "path": "rotation"
                    }
                }
            )
            animation_samplers.append(
                {
                    "input": animation_input_index,
                    "output": rotation
                }
            )
            
            # Scale
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {
                        "node": node_index,
                        "path": "scale"
                    }
                }
            )
            animation_samplers.append(
                {
                    "input": animation_input_index,
                    "output": scale
                }
            )

        animations.append(
            {
                "name": "clip",
                "channels": animation_channels,
                "samplers": animation_samplers
            }
        )
        
        self.json["animations"] = animations
        
        self.process_animation_skin(used_nodes)
        
    def process_animation_skin(self, nodes: list[int]) -> None:
        skins: list[dict] = self.json.get("skins", [])
    
        for skin in skins:
            joints: list[int] = skin["joints"]
            if (all(joints, nodes)): return
            
        new_skin_joints: list[int] = []
        def add_skin_joint(idx: int):
            node = self.json["nodes"][idx]
            childrens = node.get("children", [])
            for children in childrens:
                add_skin_joint(children)
            if (idx not in new_skin_joints):
                new_skin_joints.append(idx)
        
        for node in nodes:
            add_skin_joint(node)
        
        skins.append({
            "joints": new_skin_joints
        })
        self.json["skins"] = skins
    
    def calculate_odin_positions_count(self, accessor: dict) -> int:
        array = self.decode_accessor_obj(accessor)
        max_index = np.max(array)
        return max_index + 1

    
    def initialize_odin(self) -> None:
        extensions: dict = self.json.get("extensions")
        odin = extensions.pop("SC_odin_format")
        self.odin_buffer_index = odin["bufferView"]
        
        if "materials" in odin:
            self.json["materials"] = odin["materials"]
            
        if "animation" in odin:
            self.process_animation(odin["animation"])
        
        if ("extensionsUsed" not in self.json): self.json["extensionsUsed"] = []
        self.json["extensionsUsed"].extend(SupercellOdinGLTF.UsedExtensions)
        
        if ("extensionsRequired" not in self.json): self.json["extensionsRequired"] = []
        self.json["extensionsRequired"].extend(SupercellOdinGLTF.RequiredExtensions)
        
        
    def save_buffers(self) -> bytes:
        stream = BinaryReader()
        
        buffers: list[dict] = []
        bufferView: list[dict] = []
        
        for buffer in self.buffers:
            buffer.offset = stream.pos()
            bufferView.append(
                buffer.serialize()
            )
            
            stream.write_bytes(buffer.data)
            stream.pad(-len(buffer.data) % 16)
        
        buffers.append(
            {
                "byteLength": len(stream.buffer())
            }
        )
        
        self.json["buffers"] = buffers
        self.json["bufferViews"] = bufferView
        
        return bytes(stream.buffer())
        
    
    def produce_buffers(self, data: bytes) -> None:
        if "buffers" not in self.json:
            return
        
        if "bufferViews" not in self.json:
            return
        
        buffers: list[dict] = self.json["buffers"]
        bufferViews: list[dict] = self.json["bufferViews"]
        assert(len(buffers) == 1)
        
        stream = BinaryReader(data)
        
        for bufferView in bufferViews:
            buffer_index = bufferView.get("buffer")
            assert(buffer_index == 0)
            
            offset = bufferView.get("byteOffset", 0)
            length = bufferView.get("byteLength")
            
            stream.seek(offset)
            data = stream.read_bytes(length)
            
            buffer = BufferView()
            buffer.stride = bufferView.get("byteStride", None)
            buffer.data = data
            self.buffers.append(buffer)
            
    
    def save(self) -> glTF:
        data = self.save_buffers()
        
        file = glTF()
        json = glTF_Chunk("JSON", self.json)
        binary = glTF_Chunk("BIN\0", data)
        file.chunks.append(json)
        file.chunks.append(binary)
        
        return file
    
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/da2172c284cd0576e3a63234ea893f9b4edcacca/addons/io_scene_gltf2/io/imp/gltf2_io_binary.py#L123
    def decode_accessor_obj(self, accessor: dict) -> np.array:
        # MAT2/3 have special alignment requirements that aren't handled. But it
        # doesn't matter because nothing uses them.
        assert accessor.get("type") not in ['MAT2', 'MAT3']

        dtype = ComponentType.to_numpy_dtype(accessor.get("componentType"))
        component_nb = DataType.num_elements(accessor.get("type"))

        buffer_view_index = accessor.get("bufferView")
        if buffer_view_index is not None:
            bufferView = self.json["bufferViews"][buffer_view_index]
            buffer_data = self.buffers[buffer_view_index].data

            accessor_offset = accessor.get("byteOffset") or 0

            bytes_per_elem = dtype(1).nbytes
            default_stride = bytes_per_elem * component_nb
            stride = bufferView.get("byteStride") or default_stride

            if stride == default_stride:
                array = np.frombuffer(
                    buffer_data,
                    dtype=np.dtype(dtype).newbyteorder('<'),
                    count=accessor.get("count") * component_nb,
                    offset = accessor_offset
                )
                array = array.reshape(accessor.get("count"), component_nb)

            else:
                # The data looks like
                #   XXXppXXXppXXXppXXX
                # where X are the components and p are padding.
                # One XXXpp group is one stride's worth of data.
                assert stride % bytes_per_elem == 0
                elems_per_stride = stride // bytes_per_elem
                num_elems = (accessor.count - 1) * elems_per_stride + component_nb

                array = np.frombuffer(
                    buffer_data,
                    dtype=np.dtype(dtype).newbyteorder('<'),
                    count=num_elems,
                )
                assert array.strides[0] == bytes_per_elem
                array = np.lib.stride_tricks.as_strided(
                    array,
                    shape=(accessor.count, component_nb),
                    strides=(stride, bytes_per_elem),
                )

        else:
            # No buffer view; initialize to zeros
            array = np.zeros((accessor.get("count"), component_nb), dtype=dtype)

        # Normalization
        if accessor.get("normalized"):
            if accessor.component_type == 5120:  # int8
                array = np.maximum(-1.0, array / 127.0)
            elif accessor.component_type == 5121:  # uint8
                array = array / 255.0
            elif accessor.component_type == 5122:  # int16
                array = np.maximum(-1.0, array / 32767.0)
            elif accessor.component_type == 5123:  # uint16
                array = array / 65535.0

            array = array.astype(np.float32, copy=False)

        return array