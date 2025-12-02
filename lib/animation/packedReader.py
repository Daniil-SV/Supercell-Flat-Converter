from typing import List, Tuple
from lib.animation.flags import OdinAnimationFlags
from lib.animation.reader import OdinAnimationReader
import numpy as np

RotationChannels = 4
TranslationChannels = 3
ScaleChannels = 3


class OdinPackedReader(OdinAnimationReader):
    def __init__(self, gltf, animation: dict):
        super().__init__(animation)

        self.descriptor: dict = animation.get("packed")
        self.nodes: List[dict] = self.descriptor.get("nodes")
        self.stride = 12

        # Normalized transform values
        self.normalized_transform_data = gltf.decode_accessor(
            self.descriptor.get("dataAccessor"))

        # Base transform values
        self.node_base_data = gltf.decode_accessor(
            self.descriptor.get("nodeAccessor"))

        self.used_nodes = [node.get("nodeIndex") or 0 for node in self.nodes]
        self.flags = [OdinAnimationFlags(
            node.get("flags") or 0) for node in self.nodes]

        frametime = [animation.has_frametime for animation in self.flags]
        self.frame_stride = 0
        if (True in frametime and False in frametime):
            raise Exception(
                "Looks like this animation file uses mixed way of using frametime which is not supported")

        elif (True not in frametime):
            self.frame_stride = sum(
                [animation.elements_count for animation in self.flags])

        self.data = []
        self.transform_index = 0

        self.data_size = 0
        self.local_node_offset = 0
        self.node_base_data_offset = 0

    def process_node(self, node_index: int):
        node = self.nodes[node_index]
        flags = self.flags[node_index]
        total_frame_count = node.get("frameCount")
        self.data_size = node.get("dataSize")
        self.node_base_data_offset = node_index * self.stride

        # Base transform
        bTranslation = self.read_base_translation()
        bRotation = self.read_base_rotation()
        bScale = self.read_base_scale()

        translation_multiplier = self.read_base_value()
        scale_multiplier = self.read_base_value()

        # Step 1. Extracting normalized values from dataAccessor
        nTranslation, nRotation, nScale = self.read_normalized_transforms(
            total_frame_count, flags
        )

        # Step 2. Denormalizing values and filling buffers with values in raw view
        translation, rotation, scale = self.denormalize_transforms(
            total_frame_count, flags, (translation_multiplier, scale_multiplier, ),
            bTranslation, bRotation, bScale,
            nTranslation, nRotation, nScale
        )

        self.data.append((translation, rotation, scale))
        self.local_node_offset = 0
        self.node_base_data_offset = 0
        self.data_size = 0

    def denormalize_transforms(self,
                               frame_count: int, flags: OdinAnimationFlags, multiplier: Tuple[int, int],
                               bTranslation: np.array, bRotation: np.array, bScale: np.array,  # Base transform
                               nTranslation: np.array, nRotation: np.array, nScale: np.array  # Delta transforms
                               ):
        translation_multiplier, scale_multiplier = multiplier

        rotation = [
            np.zeros((frame_count), dtype=np.float32)
            for _ in range(RotationChannels)
        ]

        translation = [
            np.zeros((frame_count), dtype=np.float32)
            for _ in range(TranslationChannels)
        ]

        scale = [
            np.full((frame_count), 1, dtype=np.float32)
            for _ in range(ScaleChannels)
        ]

        for frame_index in range(frame_count):
            for i in range(TranslationChannels):
                value = float(bTranslation[i])
                if flags.has_translation:
                    transform = float(
                        nTranslation[i][frame_index]) * translation_multiplier
                    value += transform

                translation[i][frame_index] = value

            for i in range(RotationChannels):
                value = float(bRotation[i])
                if flags.has_rotation:
                    value = float(nRotation[i][frame_index]) / 32767.0

                rotation[i][frame_index] = value

            for i in range(ScaleChannels):
                value = float(bScale[i])
                if flags.has_scale or flags.has_separate_scale:
                    transform = float(
                        nScale[i][frame_index]) * scale_multiplier
                    value += transform

                scale[i][frame_index] = value

        return (translation, rotation, scale)

    def read_normalized_transforms(self, frame_count: int, flags: OdinAnimationFlags):
        node_elements_counter = 0

        rotation = [
            np.zeros((frame_count), dtype=np.int16)
            for _ in range(RotationChannels)
        ] if flags.has_rotation else None

        translation = [
            np.zeros((frame_count), dtype=np.int16)
            for _ in range(TranslationChannels)
        ] if flags.has_translation else None

        scale = [
            np.zeros((frame_count), dtype=np.int16)
            for _ in range(ScaleChannels)
        ] if (flags.has_scale or flags.has_separate_scale) else None

        for frame_index in range(frame_count):
            if (not flags.has_frametime):
                self.transform_index = (
                    self.frame_stride * frame_index) + node_elements_counter

            if (flags.has_frametime):
                # Skip for now. Idk why it exist at all. Maybe for compatibility with gltf animations
                frametime = self.read_normalized_value()

            if (flags.has_rotation):
                for i in range(RotationChannels):
                    rotation[i][frame_index] = self.read_normalized_value()

            if (flags.has_translation):
                for i in range(TranslationChannels):
                    translation[i][frame_index] = self.read_normalized_value()

            if (flags.has_scale and flags.has_separate_scale):
                for i in range(ScaleChannels):
                    scale[i][frame_index] = self.read_normalized_value()
            elif (flags.has_scale):
                value = self.read_normalized_value()
                for i in range(ScaleChannels):
                    scale[i][frame_index] = value

        return (translation, rotation, scale)

    def read_normalized_value(self) -> int | float:
        result = self.normalized_transform_data[self.transform_index]
        self.transform_index += 1
        return result

    def read_base_translation(self) -> List[int]:
        return [
            self.read_base_value()
            for _ in range(TranslationChannels)
        ]

    def read_base_rotation(self) -> List[int]:
        return [
            self.read_base_value()
            for _ in range(RotationChannels)
        ]

    def read_base_scale(self) -> List[int]:
        return [
            self.read_base_value()
            for _ in range(ScaleChannels)
        ]

    def read_base_value(self) -> int:
        idx = self.node_base_data_offset + self.local_node_offset
        self.local_node_offset += 1
        return self.node_base_data[idx]

    def read(self):
        self.keyframe_mapping = [node.get("frameCount") for node in self.nodes]
        
        for i in range(len(self.nodes)):
            self.process_node(i)

    def get_frame_data(self, node_index: int, frame_index: int) -> Tuple[list, list, list]:
        translation, rotation, scale = self.data[node_index]

        return ([channel[frame_index] for channel in translation],
                [channel[frame_index] for channel in rotation],
                [channel[frame_index] for channel in scale])
