# HomeFleet HBJSON Tools
Houdini uses a proprietary file format for point caches called `.hbjson` when exporting a special effect to Unreal Engine Niagara. Those files cannont be edited in a text editor, Houdini nor Unreal Engine, effectively making the edition of the special effects impossible without the source files. 
This repository contains tools to convert `.hbjson` files to `.json` and vice versa, as well as a Blender addon to export point caches in the `.hbjson` format expected by HomeWorld3 Niagara Special Effects.

## HBJSON Blender Addon

### Description
The HBJSON Blender Addon enables the exportation of ship engines, vector thrusters and idle lights to the HBJSON format expected by HomeWorld3 Niagara Special Effects.

### Features
- Export ship engines, idle lights and vector thrusters in Houdini Point Cache format for HW3
- Integrates into Blender's export menu

### Installation
1. Open Blender.
2. Go to `Edit > Preferences > Add-ons`.
3. Click `Install` and select the `HBJSON_BlenderAddon.py` file.
4. Enable the addon by checking the box next to "Homeworld 3 - HBJSON Exporter".

### Usage
1. Separate the engine objects inside a collection named "ENGINE", "VJETS" or "HERO LIGHTS".
2. Click on `File > Export > Houdini Point Cache (.hbjson)`.

#### Objects
The objects inside a collection marked for exportation can either be a mesh or an "Empty" object.
A mesh object will be exported by extracting normals, a dynamicly computing it's dimensions.
An "Empty" object will be exported by using it's position, rotation and scale transforms as the object's properties.
Any object that is not a mesh or an "Empty" object will be ignored during the exportation.

## HBJSON Transcoder

### Description
HBJSON Transcoder is a tool designed to convert Houdini Point Cache files between `.hbjson` and `.json` formats. The executable supports drag-and-drop functionality for easy file conversion, as well as command-line usage.

### Features
- Convert `.hbjson` files to `.json`
- Convert `.json` files to `.hbjson`
- Supports both drag-and-drop and command-line interfaces

### Building the Executable
To build the HBJSON Transcoder, follow these steps:

1. Ensure Python is installed on your system.
2. Install `cx_Freeze` using pip if not already installed:
    ```sh
    pip install cx_Freeze
    ```
3. Build the executable by running the following command:
    ```sh
    build_and_zip.bat
    ```
4. The executable will be generated in the `build` directory, and a ZIP file containing the executable and required dependencies will be created.

### Usage

#### Drag-and-Drop
1. Drag and drop a `.hbjson` or `.json` file onto the executable.
2. The file will be automatically converted to the corresponding format and saved in the same directory.

#### Command-Line
To use the HBJSON Transcoder via the command-line, execute the following command:
```sh
HBJSON_Transcoder.exe <file_path>
```
Replace `<file_path>` with the path to the file you want to convert, either a `.hbjson` or `.json` file.

### Dependencies
The following Python packages are required:
- `os`
- `struct`
- `json`

These dependencies are automatically included when building the executable.