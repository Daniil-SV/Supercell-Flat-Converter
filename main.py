import os
import json
import argparse
from lib.glTF import glTF, ObjectProcessor
from lib.odin import SupercellOdinGLTF

debug = True

required_folders = {
    "sc_input": "In-SC-glTF",
    "sc_output": "Out-SC-glTF",
    "def_input": "In-glTF",
    "def_output": "Out-glTF",
}

if (debug): 
    required_folders["in_debug"] = "In-Debug"
    required_folders["out_debug"] = "Out-Debug"

def decode(post_process: bool):
    files = os.scandir(required_folders["sc_input"])
    
    for filepath in files:
        gltf = glTF()
        
        with open(filepath.path, "rb") as file:
            gltf.read(file.read())

        for chunk in gltf.chunks:
            chunk.deserialize_json()
            
        if (post_process):
            odin = SupercellOdinGLTF(gltf)
            gltf = odin.process()
        
        if (debug):
            open(os.path.join(required_folders["out_debug"], filepath.name) + ".json", "wb").write([bytes(json.dumps(chunk.data, cls=ObjectProcessor, indent=4), "utf8") for chunk in gltf.chunks if chunk.name == "JSON"][0])
        
        print(f"Successful: {filepath.name}")
        
        with open(os.path.join(required_folders["def_output"], filepath.name), "wb") as file:
            file.write(gltf.write())

def encode():
    files = os.scandir(required_folders["def_input"])

    for filepath in files:
        print(f"Reading: {filepath.name}")
        gltf = glTF()

        with open(filepath.path, "rb") as file:
            gltf.read(file.read())

        for chunk in gltf.chunks:
            chunk.serialize_json()

        if debug:
            open(
                os.path.join(
                    required_folders["in_debug"], f"{filepath.name}.bin"
                ),
                "wb",
            ).write(
                [chunk.data for chunk in gltf.chunks if chunk.name == "FLA2"][0]
            )

        print(f"Successful: {filepath.name}")

        with open(os.path.join(required_folders["sc_output"], filepath.name), "wb") as file:
            file.write(gltf.write())

if __name__ == "__main__":
    for name in required_folders.values():
        os.makedirs(name, exist_ok=True)
        
    parser = argparse.ArgumentParser(
        prog="scglTF Converter", description="Tool for converting Supercell glTF files to usual ones and vice versa"
    )
    
    parser.add_argument("mode", type=str, choices=["decode", "decodeRaw", "encode"])
    
    args = parser.parse_args()
    if (args.mode == "decode"):
        decode(post_process=True)
    if (args.mode == "decodeRaw"):
        decode(post_process=False)
    elif (args.mode == "encode"):
        encode()