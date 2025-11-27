from typing import List
from lib.animation.flags import OdinAnimationFlags
from lib.animation.packedReader import OdinPackedReader
from lib.animation.packedReader import TranslationChannels, RotationChannels, ScaleChannels
import numpy as np


class OdinContinuousPackedReader(OdinPackedReader):
    def __init__(self, gltf, animation):
        super().__init__(gltf, animation)

        self.rotation_data = None
        rotation_accessor_idx = self.descriptor.get("uintAccessor")
        if (rotation_accessor_idx is not None):
            self.rotation_counter = 0
            self.rotation_data = gltf.decode_accessor(rotation_accessor_idx)
            self.stride = 8

        self.elements_counter = 0

    def read_normalized_transforms(self, frame_count: int, flags: OdinAnimationFlags):
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

        if (not flags.has_transform):
            return (translation, rotation, scale)

        frame_index = 0
        while (frame_count > frame_index):
            if (frame_index != 0):
                repeat_keyframe_count = int(self.read_normalized_value())

                # For some reason repeat count for latest frame is negative (some kind of optimization?)
                repeat_keyframe_count = abs(repeat_keyframe_count)

                # Repeat latest transforms for all transform channels
                for _ in range(repeat_keyframe_count):
                    if (flags.has_rotation):
                        for i in range(RotationChannels):
                            rotation[i][frame_index] = rotation[i][frame_index - 1]

                    if (flags.has_translation):
                        for i in range(TranslationChannels):
                            translation[i][frame_index] = translation[i][frame_index - 1]

                    if (flags.has_scale or flags.has_separate_scale):
                        for i in range(ScaleChannels):
                            scale[i][frame_index] = scale[i][frame_index - 1]

                    frame_index += 1

            if (frame_index >= frame_count):
                break

            keyframes_count = int(self.read_normalized_value())
            for _ in range(keyframes_count):
                # if (not flags.has_frametime):
                #    self.transform_index = (self.frame_stride * frame_index) + node_elements_counter

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

                frame_index += 1

        self.elements_counter = 0
        return (translation, rotation, scale)

    def read_normalized_value(self) -> int | float:
        result = self.normalized_transform_data[self.transform_index]
        self.transform_index += 1
        if (self.elements_counter >= self.data_size):
            raise Exception("Transform index exceeded data size limit")

        self.elements_counter += 1
        return result

    def read_base_rotation(self) -> List[int]:
        if (self.rotation_data is None):
            return super().read_base_rotation()

        result = [
            self.rotation_data[self.rotation_counter + i]
            for i in range(RotationChannels)
        ]
        self.rotation_counter += RotationChannels
        return result
