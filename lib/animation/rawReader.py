from lib.animation.reader import OdinAnimationReader
import numpy as np

class OdinRawAnimationReader(OdinAnimationReader):
    def __init__(self, gltf, animation: dict):
        super().__init__(animation)
        
        self.used_nodes = animation.get("nodes")    
        self.keyframe_mapping = animation.get("keyframeCounts")
        
        nodes_per_keyframe = animation.get("nodesNumberPerKeyframe")
        if (self.keyframe_mapping): 
            self.keyframe_mapping = [num for i, num in enumerate(self.keyframe_mapping) for _ in range(nodes_per_keyframe[i])]
        
        self.buffer = gltf.decode_accessor(animation.get("accessor")) 
        self.data: np.array = None   

    def read(self):       
        keyframes_total = sum(self.keyframe_mapping) if self.keyframe_mapping else self.keyframe_count
        
        # Position + Quaternion Rotation + Scale
        frame_transform_length = 3 + 4 + 3
        if (self.keyframe_mapping):
            remapped = np.reshape(self.buffer, (keyframes_total, frame_transform_length))
            self.data = np.split(remapped, np.cumsum(self.keyframe_mapping)[:-1])
        else:
            self.data = np.reshape(self.buffer, (len(self.used_nodes), self.keyframe_count, frame_transform_length))
    
    def get_frame_data(self, node_index: int, frame_index: int):        
        return np.array_split(self.data[node_index][frame_index], [3, 7])