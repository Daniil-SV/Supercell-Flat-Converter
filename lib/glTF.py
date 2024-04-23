from binary_reader import BinaryReader
from .flatbuffer import serialize_glb_json, deserialize_glb_json
import json

class glTF_Chunk:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self.data = data

    def serialize_json(self) -> None:
        if (self.name != "JSON"): return
        
        self.data = serialize_glb_json(
            json.loads(self.data)
        )
        self.name = "FLA2"
        
    def deserialize_json(self) -> None:
        if (self.name != "FLA2"): return
        
        self.data = bytes(
            json.dumps(deserialize_glb_json(self.data), allow_nan=False, separators=(',', ':')),
            "utf8"
        )
        self.name = "JSON"

class glTF:
    def __init__(self) -> None:
        self.chunks: list[glTF_Chunk] = []
        
    def write(self) -> bytes:
        stream = BinaryReader()
        
        stream.write_str("glTF") # Magic
        stream.write_uint32(2) # Version
        
        chunks_length = 0
        for chunk in self.chunks:
            chunks_length += len(chunk.data) + 8
        
        stream.write_uint32(len(stream.buffer()) + 4 + chunks_length)
        
        for chunk in self.chunks:
            stream.write_uint32(len(chunk.data))
            stream.write_str_fixed(chunk.name, 4)
            stream.write_bytes(chunk.data)
            
        return bytes(stream.buffer())
        
    def read(self, data: bytes) -> None:
        stream = BinaryReader(data)
        
        magic = stream.read_str(4)
        if (magic != "glTF"):
            raise Exception(f"File has corrupted magic: {magic}")
        
        version = stream.read_uint32()
        if (version != 2):
            raise Exception(f"File has unknown version: {version}")
        
        file_length = stream.read_uint32()
        if (len(data) != file_length):
            raise Exception(f"File has corrupted length: expected {file_length}")
        
        while(not stream.eof()):
            chunk_length = stream.read_uint32()
            chunk_magic = stream.read_str(4)
            chunk_data = stream.read_bytes(chunk_length)
            
            self.chunks.append(
                glTF_Chunk(chunk_magic, chunk_data)
            )
        
        