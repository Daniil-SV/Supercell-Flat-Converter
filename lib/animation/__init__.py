from lib.animation.reader import OdinAnimationReader
from lib.animation.rawReader import OdinRawAnimationReader
from lib.animation.packedReader import OdinPackedReader
from lib.animation.continuousPackedReader import OdinContinuousPackedReader

class OdinAnimation:
    @staticmethod
    def CreatePackedReader(gltf, descriptor: dict) -> OdinPackedReader:
        packed: dict = descriptor.get("packed")
        if (packed.get("uintAccessor") is not None):
            return OdinContinuousPackedReader(gltf, descriptor)
        
        return OdinPackedReader(gltf, descriptor)
    
    @staticmethod
    def Create(gltf, descriptor: dict) -> OdinAnimationReader:
        result = None
        if (descriptor.get("nodes") is not None and descriptor.get("accessor") is not None):
            result = OdinRawAnimationReader(gltf, descriptor)
        
        if (descriptor.get("packed") is not None):
            result = OdinAnimation.CreatePackedReader(gltf, descriptor)
        
        if (result is None):
            raise NotImplementedError("Unknown animation data")
        
        result.read()
        return result