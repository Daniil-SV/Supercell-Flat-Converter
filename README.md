<p align="center">
<h1 align="center" style="font-size: 32px;"> Supercell World Flatbuffer Converter </h1>
</p>

# Description
The purpose of this script is to convert Supercell glTF files that was optimized with [Flatbuffer](https://github.com/google/flatbuffers) into a regular json and then import it into any 3D software  
and also it support back conversion just in case

# How to use
You must have Python 3.10+ to use it  
First, clone or download repository and open console in folder with repository content  
Then run ```py main.py``` to create folders  
To convert optimized files to regular glb files, put your files in ```In-SC-glTF``` folder and run ```py main.py decode```. Result will be stored in ```Out-glTF``` folder.
And to convert regular glb files to optimized, put your files in ```In-glTF``` folder, run ```py main.py encode```. Output will be stored in ```Out-SC-glTF``` folder.

!! BUG !!  
Optimized animation files crashes for some unknown reason.

# How to 'Build'
Flatc is used here to generate an API for obtaining information from binary data, and if you want to change the scheme, make sure that the flatc is available for execution and to generate run ```generate.bat```