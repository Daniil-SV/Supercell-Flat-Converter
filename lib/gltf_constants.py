from enum import IntEnum


class ComponentType(IntEnum):
    Byte = 5120
    UnsignedByte = 5121
    Short = 5122
    UnsignedShort = 5123
    UnsignedInt = 5125
    Float = 5126

    @classmethod
    def to_type_code(cls, component_type):
        return {
            ComponentType.Byte: 'b',
            ComponentType.UnsignedByte: 'B',
            ComponentType.Short: 'h',
            ComponentType.UnsignedShort: 'H',
            ComponentType.UnsignedInt: 'I',
            ComponentType.Float: 'f'
        }[component_type]

    @classmethod
    def to_numpy_dtype(cls, component_type):
        import numpy as np
        return {
            ComponentType.Byte: np.int8,
            ComponentType.UnsignedByte: np.uint8,
            ComponentType.Short: np.int16,
            ComponentType.UnsignedShort: np.uint16,
            ComponentType.UnsignedInt: np.uint32,
            ComponentType.Float: np.float32,
        }[component_type]

    @classmethod
    def get_size(cls, component_type):
        return {
            ComponentType.Byte: 1,
            ComponentType.UnsignedByte: 1,
            ComponentType.Short: 2,
            ComponentType.UnsignedShort: 2,
            ComponentType.UnsignedInt: 4,
            ComponentType.Float: 4
        }[component_type]


class DataType:
    Scalar = "SCALAR"
    Vec2 = "VEC2"
    Vec3 = "VEC3"
    Vec4 = "VEC4"
    Mat2 = "MAT2"
    Mat3 = "MAT3"
    Mat4 = "MAT4"

    def __new__(cls, *args, **kwargs):
        raise RuntimeError(f"{cls.__name__} should not be instantiated")

    @classmethod
    def num_elements(cls, data_type):
        return {
            DataType.Scalar: 1,
            DataType.Vec2: 2,
            DataType.Vec3: 3,
            DataType.Vec4: 4,
            DataType.Mat2: 4,
            DataType.Mat3: 9,
            DataType.Mat4: 16
        }[data_type]

    @classmethod
    def vec_type_from_num(cls, num_elems):
        if not (0 < num_elems < 5):
            raise ValueError(f"No vector type with {num_elems} elements")
        return {
            1: DataType.Scalar,
            2: DataType.Vec2,
            3: DataType.Vec3,
            4: DataType.Vec4
        }[num_elems]

    @classmethod
    def mat_type_from_num(cls, num_elems):
        if not (4 <= num_elems <= 16):
            raise ValueError(f"No matrix type with {num_elems} elements")
        return {
            4: DataType.Mat2,
            9: DataType.Mat3,
            16: DataType.Mat4
        }[num_elems]
