from enum import IntEnum
import numpy as np


class OdinAttributeType(IntEnum):
    a_pos = 0
    a_normal = 1
    a_uv0 = 2
    a_uv1 = 3
    a_color = 4
    a_boneindex = 5
    a_boneweights = 6
    a_tangent = 7
    a_colorMul = 8
    a_colorAdd = 9
    a_model = 10
    a_model2 = 11
    a_model3 = 12
    a_binormal = 13
    a_skinningOffsets = 14
    
    @classmethod
    def to_attribute_name(cls, component_type) -> str:
        return {
            OdinAttributeType.a_pos: 'POSITION',
            OdinAttributeType.a_normal: 'NORMAL',
            OdinAttributeType.a_boneindex: 'JOINTS_0',
            OdinAttributeType.a_boneweights: 'WEIGHTS_0',
            OdinAttributeType.a_uv0: 'TEXCOORD_0',
            OdinAttributeType.a_uv1: 'TEXCOORD_1',
            OdinAttributeType.a_color: 'COLOR_0',
        }[component_type]


class OdinAttributeFormat(IntEnum):
    UByteVector4 = 3
    ColorRGBA = 9
    UByteVector3 = 12
    FloatVector2 = 29
    FloatVector3 = 30
    NormalizedWeightVector = 36
    
    @classmethod
    def to_accessor_type(cls, component_type) -> str:
        return {
            OdinAttributeFormat.FloatVector3: 'VEC3',
            OdinAttributeFormat.UByteVector3: 'VEC3',
            OdinAttributeFormat.UByteVector4: 'VEC4',
            OdinAttributeFormat.NormalizedWeightVector: 'VEC4',
            OdinAttributeFormat.FloatVector2: 'VEC2',
            OdinAttributeFormat.ColorRGBA: 'VEC4',
        }[component_type]
    
    @classmethod
    def to_accessor_component(cls, component_type) -> int:
        return {
            OdinAttributeFormat.FloatVector3: 5126,
            OdinAttributeFormat.UByteVector3: 5120,
            OdinAttributeFormat.UByteVector4: 5121,
            OdinAttributeFormat.NormalizedWeightVector: 5126,
            OdinAttributeFormat.FloatVector2: 5126,
            OdinAttributeFormat.ColorRGBA: 5121,
        }[component_type]
        
    @classmethod
    def to_numpy_dtype(cls, component_type):
        return {
            OdinAttributeFormat.FloatVector3: np.uint32,
            OdinAttributeFormat.UByteVector3: np.byte,
            OdinAttributeFormat.UByteVector4: np.ubyte,
            OdinAttributeFormat.NormalizedWeightVector: np.float32,
            OdinAttributeFormat.FloatVector2: np.float32,
            OdinAttributeFormat.ColorRGBA: np.ubyte,
        }[component_type]
        
    @classmethod
    def to_element_count(cls, component_type) -> int:
        return {
            OdinAttributeFormat.FloatVector3: 3,
            OdinAttributeFormat.UByteVector3: 3,
            OdinAttributeFormat.UByteVector4: 4,
            OdinAttributeFormat.NormalizedWeightVector: 4,
            OdinAttributeFormat.FloatVector2: 2,
            OdinAttributeFormat.ColorRGBA: 4,
        }[component_type]
