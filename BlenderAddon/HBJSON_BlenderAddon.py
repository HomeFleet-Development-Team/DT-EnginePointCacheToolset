bl_info = {
    "name": "Homeworld 3 - HBJSON Exporter",
    "description": "Export engines, lights or vector thrusters in Houdini Point Cache format for HomeWorld3.",
    "location": "File > Export > Houdini Point Cache (.hbjson)",
    "warning": "",
    "doc_url": "https://github.com/HomeFleet-Development-Team/DT-EnginePointCacheToolset",
    "author": "Chokepoint Games, HomeFleet Development Team",
    "version": (1, 2),
    "blender": (4, 0, 0),
    "category": "Import-Export",
}

import bpy
import json
import os
import copy
import struct
import mathutils
import numpy as np
from collections import Counter

class HBJsonGenerator:
    def __init__(self):
        self.template = {
            "header": {
                "version": "1.0",
                "num_samples": 0,
                "num_frames": 1,
                "num_points": 0,
                "num_attrib": 20,
                "attrib_name": [
                    "id",
                    "InitialSpriteSizeX",
                    "InitialSpriteSizeY",
                    "Alpha",
                    "Color",
                    "class",
                    "pscale",
                    "CameraOffset",
                    "Age",
                    "age",
                    "P",
                    "DynamicMaterialParameterW",
                    "Life",
                    "DynamicMaterialParameterX",
                    "Cd",
                    "DynamicMaterialParameterY",
                    "DynamicMaterialParameterZ",
                    "hitnormal",
                    "aligntosurface",
                    "MaterialOption",
                ],
                "attrib_size": [
                    1,
                    1,
                    1,
                    1,
                    3,
                    1,
                    1,
                    1,
                    1,
                    1,
                    3,
                    1,
                    1,
                    1,
                    3,
                    1,
                    1,
                    3,
                    1,
                    1
                ],
                "attrib_data_type": [
                    108,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    108,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    102,
                    108,
                    108
                ],
                "data_type": "linear"
            },
            "cache_data": {
                "frames": [
                    {
                        "number": 0,
                        "time": 0,
                        "num_points": 0,
                        "frame_data": []
                    }
                ]
            }
        }

    def generate_json(self, input_data):
        output = copy.deepcopy(self.template)
        output["header"]["num_samples"] = len(input_data)
        output["header"]["num_points"] = len(input_data)
        output["cache_data"]["frames"][0]["num_points"] = len(input_data)

        inputs_max_dimension = max([max(point["dimensions"]) for point in input_data])

        frame_data = []
        for i, point in enumerate(input_data):
            location = point["location"]
            dimensions = point["dimensions"]
            normal = point["normal"]
            max_dimension = max(dimensions)
            sprite_size = max_dimension * 500
            pscale = max_dimension / inputs_max_dimension

            point_data = [
                [i],  # id
                [sprite_size],  # InitialSpriteSizeX
                [sprite_size],  # InitialSpriteSizeY
                [1.0],  # Alpha
                [1.0, 1.0, 1.0],  # Color
                [0.0],  # class
                [pscale],  # pscale
                [1073741824],  # CameraOffset
                [0.0],  # Age
                [0.0],  # age
                location,  # P
                [1.0],  # DynamicMaterialParameterW
                [1.0],  # Life
                [1.0],  # DynamicMaterialParameterX
                [1.0, 1.0, 1.0],  # Cd
                [1.0],  # DynamicMaterialParameterY
                [1.0],  # DynamicMaterialParameterZ
                normal,  # hitnormal
                [1.401298464324817e-45],  # aligntosurface
                [0.0]  # MaterialOption
            ]

            frame_data.append(point_data)

        output["cache_data"]["frames"][0]["frame_data"] = frame_data
        return output

class ObjectMetaProperty(bpy.types.PropertyGroup):
    location: bpy.props.FloatVectorProperty(name="Location", size=3)
    dimensions: bpy.props.FloatVectorProperty(name="Dimensions", size=3)
    normal: bpy.props.FloatVectorProperty(name="Normal", size=3)

class HBJsonPropertyGroup(bpy.types.PropertyGroup):
    json: bpy.props.StringProperty()

class SaveHBJSONOperator(bpy.types.Operator):
    bl_idname = "wm.save_hbjson"
    bl_label = "Save Point Cache"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    buffer = bytearray()

    MarkerTypeChar = ord(b'c')
    MarkerTypeInt8 = ord(b'b')
    MarkerTypeUInt8 = ord(b'B')
    MarkerTypeBool = ord(b'?')
    MarkerTypeInt16 = ord(b'h')
    MarkerTypeUInt16 = ord(b'H')
    MarkerTypeInt32 = ord(b'l')
    MarkerTypeUInt32 = ord(b'L')
    MarkerTypeInt64 = ord(b'q')
    MarkerTypeUInt64 = ord(b'Q')
    MarkerTypeFloat32 = ord(b'f')
    MarkerTypeFloat64 = ord(b'd')
    MarkerTypeString = ord(b's')
    MarkerObjectStart = ord(b'{')
    MarkerObjectEnd = ord(b'}')
    MarkerArrayStart = ord(b'[')
    MarkerArrayEnd = ord(b']')

    def write_marker(self, marker):
            self.buffer.append(marker)

    def write_uint8_string(self, string):
        self.buffer.append(len(string))
        self.buffer.extend(string.encode('utf-8'))

    def write_uint32(self, value):
        self.buffer.extend(struct.pack('I', value))

    def write_uint16(self, value):
        self.buffer.extend(struct.pack('H', value))

    def write_list(self, list_data):
        self.write_marker(self.MarkerArrayStart)
        for item in list_data:
            if isinstance(item, str):
                self.write_marker(self.MarkerTypeUInt8)
                self.write_uint8_string(item)
            elif isinstance(item, dict):
                self.write_marker(self.MarkerObjectStart)
                self.write_object(item)
                self.write_marker(self.MarkerObjectEnd)
            elif isinstance(item, list):
                self.write_list(item)
            else:
                self.write_marker(item)

        self.write_marker(self.MarkerArrayEnd)

    def write_object(self, obj):
        for key, value in obj.items():
            self.write_marker(self.MarkerTypeUInt8)
            self.write_uint8_string(key)

            if isinstance(value, int):
                if key in ["num_samples", "num_frames", "num_points", "number", "time"]:
                    self.write_uint32(value)
                elif key in ["num_attrib"]:
                    self.write_uint16(value)
            elif isinstance(value, list):
                if key == "frame_data":
                    self.write_frames_data(value)
                else:
                    self.write_list(value)
            elif isinstance(value, dict):
                self.write_marker(self.MarkerObjectStart)
                self.write_object(value)
                self.write_marker(self.MarkerObjectEnd)
            else:
                self.write_marker(self.MarkerTypeUInt8)
                self.write_uint8_string(str(value))

    def write_frames_data(self, frames_data):
        self.write_marker(self.MarkerArrayStart)
        for frame in frames_data:
            self.write_marker(self.MarkerArrayStart)
            for attribute in frame:
                if all(isinstance(i, int) for i in attribute):
                    for item in attribute:
                        self.buffer.extend(struct.pack('i', item))
                elif all(isinstance(i, float) for i in attribute):
                    for item in attribute:
                        self.buffer.extend(struct.pack('f', item))
            self.write_marker(self.MarkerArrayEnd)
        self.write_marker(self.MarkerArrayEnd)

    def execute(self, context):
        data_to_save = json.loads(context.scene.json_data[0].json)
        self.write_marker(self.MarkerObjectStart)
        self.write_object(data_to_save)
        self.write_marker(self.MarkerObjectEnd)
        with open(self.filepath, 'wb') as f:
            f.write(self.buffer)
        self.report({'INFO'}, f"HBJSON saved to {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # Set the default filename to JSON_<PROJECTNAME>.json
        blend_file_path = bpy.data.filepath
        project_name = os.path.splitext(os.path.basename(blend_file_path))[0]
        default_filename = f"FX_HJ_<FACTION>_{project_name}_{context.scene.point_cache_type}.hbjson"
        self.filepath = os.path.join(os.path.dirname(blend_file_path), default_filename)
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ExportEnginesOperator(bpy.types.Operator):
    bl_idname = "wm.export_engines"
    bl_label = "Houdini Point Cache (.hbjson)"
    bl_description = "Export engines, lights or vector thrusters in Houdini Point Cache format for HW3."

    def execute(self, context):
        collections = bpy.data.collections

        target = None
        export_type = None

        for collection in collections:
            is_active = collection == bpy.context.view_layer.active_layer_collection.collection
            is_visible = collection.hide_viewport == False
            is_render_enabled = collection.hide_render == False

            if not is_active or not is_visible or not is_render_enabled:
                continue

            if "engine" in collection.name.lower():
                target = collection
                export_type = "Engines"
                break

            if "thruster" in collection.name.lower() or "vector" in collection.name.lower() or "vjets" in collection.name.lower():
                target = collection
                export_type = "VJets"
                break
            
            if "light" in collection.name.lower() or "idle" in collection.name.lower() or "hero" in collection.name.lower():
                target = collection
                export_type = "HERO"
                break

        if not target:
            self.report({'ERROR'}, "No \"Engines\", \"Vjets\" or \"Hero\" collection found.")
        else:
            objects = target.objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select_set(True)
            
            context.scene.objects_meta.clear()

            for obj in objects:
                if obj.type == 'EMPTY':
                    matrix = obj.matrix_world
                    normal_vector = matrix.to_3x3() @ mathutils.Vector((0, 0, 1))
                    normal_vector.normalize()
                    
                    meta = context.scene.objects_meta.add()
                    meta.location = obj.location
                    meta.dimensions = obj.scale
                    meta.normal = normal_vector
                    continue

                if obj.type == 'MESH':
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)

                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

                    meta = context.scene.objects_meta.add()
                    meta.location = obj.location
                    meta.dimensions = obj.dimensions

                    mesh = obj.data
                    normals = [l.normal.copy().freeze() for l in mesh.loops]
                    common_normal = Counter(normals).most_common(1)[0][0]
                    meta.normal = common_normal
                    obj.select_set(False)
                    continue
                self.report({'WARNING'}, f"Object {obj.name} is not a mesh or empty object and as been ignored for " + export_type + " export.")

            hb_json_generator = HBJsonGenerator()
            raw_engine_data = [{'location': list(meta.location), 'dimensions': list(meta.dimensions), 'normal':list(meta.normal)} for meta in context.scene.objects_meta]
            json_data = hb_json_generator.generate_json(raw_engine_data)
            context.scene.json_data.clear()
            context.scene.json_data.add()
            context.scene.json_data[0].json = json.dumps(json_data)
            context.scene.point_cache_type = export_type


            bpy.ops.wm.save_hbjson('INVOKE_DEFAULT')
        return {'FINISHED'}


def export_menu_func(self, context):
    self.layout.operator(ExportEnginesOperator.bl_idname)

def register():
    bpy.utils.register_class(ObjectMetaProperty)
    bpy.utils.register_class(HBJsonPropertyGroup)
    bpy.utils.register_class(SaveHBJSONOperator)
    bpy.utils.register_class(ExportEnginesOperator)
    bpy.types.TOPBAR_MT_file_export.append(export_menu_func)
    bpy.types.Scene.objects_meta = bpy.props.CollectionProperty(type=ObjectMetaProperty)
    bpy.types.Scene.json_data = bpy.props.CollectionProperty(type=HBJsonPropertyGroup)
    bpy.types.Scene.point_cache_type = bpy.props.StringProperty(name="Point Cache Type")

def unregister():
    bpy.utils.unregister_class(ObjectMetaProperty)
    bpy.utils.unregister_class(HBJsonPropertyGroup)
    bpy.utils.unregister_class(SaveHBJSONOperator)
    bpy.utils.unregister_class(ExportEnginesOperator)
    bpy.types.TOPBAR_MT_file_export.remove(export_menu_func)
    del bpy.types.Scene.objects_meta
    del bpy.types.Scene.json_data

    # Remove the option if it already exists
    bpy.types.TOPBAR_MT_window.remove(export_menu_func)

if __name__ == "__main__":
    register()
