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
        self.stride: int | None = None
        self.data: bytes = b''
        self.offset: int | None = None
        
    def serialize(self):
        data = {
            "buffer": 0,
            "byteOffset": self.offset,
            "byteLength": len(self.data),
        }
        
        if self.stride is not None:
            data["byteStride"] = self.stride
            
        return data

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
        if isinstance(self.json, bytes):
            self.json = json.loads(self.json)
        self.buffers: list[BufferView] = []
        self.odin_buffer_index: int = -1
        self.mesh_descriptors: list[dict] = []
        self.cached_mesh_descriptors: dict = {}
        
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
            
    def create_primitive_cache(self, meshes: list[dict]) -> None:
        vertex_count = {}
        descriptors = {}
        
        for mesh in meshes:
            primitives = mesh.get("primitives")
            if (primitives is None): continue
            
            for primitive in primitives:
                extensions: dict = primitive.get("extensions", {})
                if "SC_odin_format" not in extensions: continue
                
                odin: dict = extensions["SC_odin_format"]
                indices = primitive.get("indices")
                count = self.calculate_odin_positions_count(self.json["accessors"][indices])
            
                info_index = odin.get("meshDataInfoIndex")
                mesh_descriptor = odin if "vertexDescriptors" in odin else self.mesh_descriptors[info_index]
                vertex_descriptors: list[dict] = mesh_descriptor["vertexDescriptors"]
                
                if info_index not in descriptors:
                    descriptors[info_index] = vertex_descriptors
                
                if (info_index in vertex_count):
                    vertex_count[info_index] = max(vertex_count[info_index], count)
                else:
                    vertex_count[info_index] = count
        
        for idx, vertex_descriptors in descriptors.items():
            attributes = {}
            for descriptor in vertex_descriptors:
                self.process_odin_primitive_descriptor(descriptor, attributes, vertex_count[idx])
                
            self.cached_mesh_descriptors[idx] = attributes
                
                
            
    def process_meshes(self) -> None:
        meshes: list[dict] = self.json.get("meshes", [])
        self.create_primitive_cache(meshes)
        
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
        
        odin: dict = extensions.pop("SC_odin_format")
        indices = primitive.get("indices")
        count = self.calculate_odin_positions_count(self.json["accessors"][indices])
        
        info_index = odin.get("meshDataInfoIndex")
        mesh_descriptor = odin if "vertexDescriptors" in odin else self.mesh_descriptors[info_index]
        vertex_descriptors: list[dict] = mesh_descriptor["vertexDescriptors"]
        
        attributes = {}
        
        if (info_index in self.cached_mesh_descriptors):
            attributes = self.cached_mesh_descriptors[info_index]
        else:
            for descriptor in vertex_descriptors:
                self.process_odin_primitive_descriptor(descriptor, attributes, count)
            self.cached_mesh_descriptors[info_index] = attributes
        
        
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
            isInteger = attribute.get("interpretAsInteger")
            attribute = OdinAttribute(
                attribute_type,
                attribute_format,
                attribute["offset"]
            )
            
            attribute_buffers.append(np.zeros((positions_count, attribute.elements_count), dtype=attribute.data_type))
            attribute_descriptor.append(attribute)
            accessor = {
                    "bufferView": len(self.buffers) + i,
                    "componentType": OdinAttributeFormat.to_accessor_component(attribute_format),
                    "count": int(positions_count),
                    "type": OdinAttributeFormat.to_accessor_type(attribute_format)
                }
            if isInteger is not None:
                accessor["normalized"] = isInteger == False
            else:
                accessor["normalized"] = OdinAttributeFormat.is_normalized(attribute_format)
                
            attribute_accessors.append(accessor)
        
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
        
        frame_rate = animation.get("frameRate") or 30
        frame_spf = 1.0 / frame_rate
        keyframes_count = (animation.get("keyframesCount") or animation.get("keyframeCount")) or 1  
        nodes_per_keyframe = animation.get("nodesNumberPerKeyframe")
        individual_keyframes_count = animation.get("keyframeCounts")
        used_nodes = animation.get("nodes")
        odin_animation_accessor = animation.get("accessor")
        node_indices = None
        
        if (individual_keyframes_count): 
            individual_keyframes_count = [num for i, num in enumerate(individual_keyframes_count) for _ in range(nodes_per_keyframe[i])]
        
        get_transform_function = None
        
        # Usual nodes
        if (used_nodes is not None and odin_animation_accessor is not None):
            animation_transform_array = self.decode_accessor_obj(self.json["accessors"][odin_animation_accessor])
            
            keyframes_total = sum(individual_keyframes_count) if individual_keyframes_count else keyframes_count
        
                    # Position + Quaternion Rotation + Scale
            frame_transform_length = 3 + 4 + 3
            if (individual_keyframes_count):
                animation_transform_array = np.reshape(animation_transform_array, (keyframes_total, frame_transform_length))
                animation_transform_array = np.split(animation_transform_array, np.cumsum(individual_keyframes_count)[:-1])
            else:
                animation_transform_array = np.reshape(animation_transform_array, (len(used_nodes), keyframes_count, frame_transform_length))
                
            def get_transform_from_raw_array(node_index, frame_index):
                return np.array_split(animation_transform_array[node_index][frame_index], [3, 7])
                
            get_transform_function = get_transform_from_raw_array
            
        # Packed nodes
        else:
            packed = animation.get("packed")
            nodes = packed.get("nodes")
            data_accessor_idx = packed.get("dataAccessor")
            node_accessor_idx = packed.get("nodeAccessor")
            individual_keyframes_count = [node.get("frameCount") or 1 for node in nodes]

            used_nodes = [node.get("nodeIndex") or 0 for node in nodes]
            
            # Base transform values
            node_base_data = self.decode_accessor_obj(self.json["accessors"][node_accessor_idx])
            
            # Normalized transform values
            normalized_transform_data = self.decode_accessor_obj(self.json["accessors"][data_accessor_idx])
            transform_index = 0

            transform_buffer = []
            
            rotation_channels = 4
            translation_channels = 3
            scale_channels = 3
            node_base_data_stride = 12
            
            #elements_counter = 0
            
            for node_index, node in enumerate(nodes):
                flags = node.get("flags") or 0xFF
                frame_count = node.get("frameCount")
                node_base_data_offset = node_index * node_base_data_stride

                has_frametime = flags & 1 != 0
                has_rotation = flags & 2 != 0
                has_translation = flags & 4 != 0
                has_single_scale = flags & 8 != 0
                has_scale = flags & 16 != 0
                
                #node_elements_counter = 0
                #if (has_frametime): node_elements_counter += 1
                #if (has_rotation): node_elements_counter += 4
                #if (has_translation): node_elements_counter += 3
                #if (has_single_scale and has_scale):
                #    node_elements_counter += 3
                #elif (has_single_scale):
                #    node_elements_counter += 1

                #elements_counter += node_elements_counter * frame_count

                # Allocating memory buffers
                
                # Base values
                node_base_translation = [
                    node_base_data[node_base_data_offset],
                    node_base_data[node_base_data_offset + 1],
                    node_base_data[node_base_data_offset + 2]
                ]
                
                node_base_rotation = [
                    node_base_data[node_base_data_offset + 3],
                    node_base_data[node_base_data_offset + 4],
                    node_base_data[node_base_data_offset + 5],
                    node_base_data[node_base_data_offset + 6],
                ]
                
                node_base_scale = [
                    node_base_data[node_base_data_offset + 7],
                    node_base_data[node_base_data_offset + 8],
                    node_base_data[node_base_data_offset + 9]
                ]
                
                # Multiply values for translation and scale data
                translation_multiplier = node_base_data[node_base_data_offset + 10]
                scale_multiplier = node_base_data[node_base_data_offset + 11]
                
                # Normalized
                node_norm_rotation = [
                        np.zeros((frame_count), dtype=np.int16)
                        for _ in range(rotation_channels)
                ]
                
                node_norm_translation = [
                        np.zeros((frame_count), dtype=np.int16)
                        for _ in range(translation_channels)
                ]

                node_norm_scale = [
                        np.zeros((frame_count), dtype=np.int16)
                        for _ in range(scale_channels)
                ]
                
                # Final (Raw)
                node_rotation = [
                        np.zeros((frame_count), dtype=np.float32)
                        for _ in range(rotation_channels)
                ]
                
                node_translation = [
                        np.zeros((frame_count), dtype=np.float32)
                        for _ in range(translation_channels)
                ]

                node_scale = [
                        np.fill((frame_count), 1, dtype=np.float32)
                        for _ in range(scale_channels)
                ]

                # Step 1. Extracting normalized values from dataAccessor
                for frame_index in range(frame_count):
                    if (has_frametime):
                        # Skip for now. Idk why it exist at all. Maybe for compatibility with gltf animations
                        frametime = normalized_transform_data[transform_index]
                        transform_index += 1
                    
                    if (has_rotation):
                        for i in range(rotation_channels):
                             node_norm_rotation[i][frame_index] = normalized_transform_data[transform_index]
                             transform_index += 1
                    
                    if (has_translation):
                        for i in range(translation_channels):
                             node_norm_translation[i][frame_index] = normalized_transform_data[transform_index]
                             transform_index += 1

                    if (has_single_scale and has_scale):
                        for i in range(scale_channels):
                            node_norm_scale[i][frame_index] = normalized_transform_data[transform_index]
                            transform_index += 1
                    elif (has_single_scale):
                        for i in range(scale_channels):
                             node_norm_scale[i][frame_index] = normalized_transform_data[transform_index]
                        transform_index += 1
                
                # Step 2. Denormalizing values and filling buffers with values in raw view
                for frame_index in range(frame_count):
                    for i in range(translation_channels):
                        value = float(node_base_translation[i])
                        if has_translation:
                            transform = float(node_norm_translation[i][frame_index]) * translation_multiplier
                            value += transform
                        
                        node_translation[i][frame_index] = value
                        
                    for i in range(rotation_channels):
                        value = float(node_base_rotation[i])
                        if has_rotation:
                            value = float(node_norm_rotation[i][frame_index]) / 32767
                        
                        node_rotation[i][frame_index] = value
                        
                    for i in range(scale_channels):
                        value = float(node_base_scale[i])
                        if has_scale or has_single_scale:
                            transform = float(node_norm_scale[i][frame_index]) * scale_multiplier
                            value += transform
                        
                        node_scale[i][frame_index] = value

                transform_buffer.append(
                    (
                        node_translation,
                        node_rotation,
                        node_scale
                    )
                )
            
            #print (elements_counter)
            
            def get_transform_from_packed_array(node_index, frame_index):
                translation, rotation, scale = transform_buffer[node_index]
                
                return ([channel[frame_index] for channel in translation], 
                        [channel[frame_index] for channel in rotation], 
                        [channel[frame_index] for channel in scale])
            
            get_transform_function = get_transform_from_packed_array
        
        # Animation input
        animation_input_index = None
        individual_input_index = None
        
        def create_input_buffer(count: int) -> int:
            result = len(self.json["accessors"])
            animation_input_buffer = BinaryReader()
            for i in range(count):
                animation_input_buffer.write_float(frame_spf * i)
            self.json["accessors"].append(
                {
                    "bufferView": len(self.buffers),
                    "componentType": 5126,
                    "count": count,
                    "type": "SCALAR"
                }
            )
            buffer_view = BufferView()
            buffer_view.data = bytes(animation_input_buffer.buffer())
            self.buffers.append(buffer_view)
            return result
        
        if (individual_keyframes_count):
            individual_input_index = {
                num: 0 for num in individual_keyframes_count
            }
            
            for num in individual_input_index.keys():
                individual_input_index[num] = create_input_buffer(num)
                
        else:
            animation_input_index = create_input_buffer(keyframes_count)

        # Animation Transform
        animation_buffers_indices: list[tuple[int, int, int]] = []
        animation_transform_buffers: list[list[BinaryReader, BinaryReader, BinaryReader]] = [[BinaryReader() for _ in range(3)] for _ in used_nodes]

        for node_index in range(len(used_nodes)):
            node_keyframes = individual_keyframes_count[node_index] if individual_keyframes_count else keyframes_count
            
            for frame_index in range(node_keyframes):
                translation, rotation, scale = animation_transform_buffers[node_index]
                t, r, s = get_transform_function(node_index, frame_index)

                for value in t:
                    translation.write_float(value)
                
                for value in r:
                    rotation.write_float(value)
                
                for value in s:
                    scale.write_float(value)

        for idx, buffer in enumerate(animation_transform_buffers):
            translation, rotation, scale = buffer
            base_accessor_index = len(self.json["accessors"])
            base_bufferView_index = len(self.buffers)
            node_keyframes = individual_keyframes_count[idx] if individual_keyframes_count else keyframes_count
            
            # Translation
            self.json["accessors"].append(
                {
                    "bufferView": base_bufferView_index,
                    "componentType": 5126,
                    "count": node_keyframes,
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
                    "count": node_keyframes,
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
                    "count": node_keyframes,
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
            if (node_indices is not None):
                node_index = node_indices[node_index]
            translation, rotation, scale = animation_buffers_indices[node_number]
            
            input_index = individual_input_index[individual_keyframes_count[node_number]] if individual_keyframes_count else animation_input_index
            
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
                    "input": input_index,
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
                    "input": input_index,
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
                    "input": input_index,
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
            if (all(joints) and all(nodes)): return
            
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
        odin: dict = extensions.pop("SC_odin_format")
        self.odin_buffer_index = odin["bufferView"]
        self.mesh_descriptors = odin.get("meshDataInfos", [])
        
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
