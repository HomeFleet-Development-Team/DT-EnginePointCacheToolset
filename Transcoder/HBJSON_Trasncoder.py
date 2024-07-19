import struct
import json
import sys
import os

class HoudiniPointCacheLoaderBJSON:
    def __init__(self, file_path):
        self.file_path = file_path
        self.reader = None
        self.position = 0

        # Marker definitions
        self.markers = {
            "char": ord(b'c'), "int8": ord(b'b'), "uint8": ord(b'B'), "bool": ord(b'?'), 
            "int16": ord(b'h'), "uint16": ord(b'H'), "int32": ord(b'l'), "uint32": ord(b'L'), 
            "int64": ord(b'q'), "uint64": ord(b'Q'), "float32": ord(b'f'), "float64": ord(b'd'), 
            "string": ord(b's'), "object_start": ord(b'{'), "object_end": ord(b'}'), 
            "array_start": ord(b'['), "array_end": ord(b']')
        }

        self.headers = {
            "uint32": ["num_samples", "num_frames", "num_points", "number", "time"],
            "uint16": ["num_attrib"],
            "list": ["attrib_name", "attrib_size"],
            "type_list": ["attrib_data_type"]
        }

        self.num_samples = 0
        self.num_frames = 0
        self.num_points = 0
        self.num_attrib = 0
        self.attrib_name = []
        self.attrib_size = []
        self.attrib_type = []

    def load(self):
        with open(self.file_path, 'rb') as file:
            self.reader = file.read()
        
        if not self.reader:
            print("Failed to read file.")
            return False

        if self.read_marker() != self.markers["object_start"]:
            print("Invalid file format.")
            return False

        return self.read_object()
    
    def read_marker(self):
        return self.read_next_byte()
    
    def read_uint8_string(self):
        length = self.read_next_byte()
        return self.read_next_bytes(length).decode('utf-8')
    
    def read_uint32(self):
        return struct.unpack('I', self.read_next_bytes(4))[0]
    
    def read_uint16(self):
        return struct.unpack('H', self.read_next_bytes(2))[0]
    
    def read_list(self):
        lst = []
        while True:
            marker = self.read_marker()
            if marker == self.markers["array_end"]:
                break
            lst.append(self.parse_marker(marker))
        return lst
    
    def read_object(self):
        obj = {}
        while True:
            marker = self.read_marker()
            if marker == self.markers["object_end"]:
                break
            if marker == self.markers["uint8"]:
                key = self.read_uint8_string()
                obj[key] = self.read_value(key)
                self.update_num_values(key, obj[key])
        return obj
    
    def read_value(self, key):
        if key in self.headers["uint32"]:
            return self.read_uint32()
        if key in self.headers["uint16"]:
            return self.read_uint16()
        if key == "frame_data":
            return self.read_frames_data()

        marker = self.read_marker()
        return self.parse_marker(marker)

    def parse_marker(self, marker):
        if marker == self.markers["uint8"]:
            return self.read_uint8_string()
        if marker == self.markers["object_start"]:
            return self.read_object()
        if marker == self.markers["array_start"]:
            return self.read_list()
        return marker
    
    def update_num_values(self, key, value):
        if key == "num_samples":
            self.num_samples = value
        elif key == "num_frames":
            self.num_frames = value
        elif key == "num_points":
            self.num_points = value
        elif key == "num_attrib":
            self.num_attrib = value
        elif key == "attrib_name":
            self.attrib_name = value
        elif key == "attrib_size":
            self.attrib_size = value
        elif key == "attrib_data_type":
            self.attrib_type = value
    
    def read_frames_data(self):
        if self.read_marker() != self.markers["array_start"]:
            print("Invalid file format.")
            return False
        
        frame_data = [self.read_frame() for _ in range(self.num_points)]
        
        if self.read_marker() != self.markers["array_end"]:
            print("Invalid file format.")
            return False
        
        return frame_data
    
    def read_frame(self):
        if self.read_marker() != self.markers["array_start"]:
            print("Invalid file format.")
            return False
        
        frame = [self.read_attribute(i) for i in range(self.num_attrib)]

        if self.read_marker() != self.markers["array_end"]:
            print("Invalid file format.")
            return False
        
        return frame
    
    def read_attribute(self, i):
        attribute_type = self.attrib_type[i]
        attribute_size = self.attrib_size[i]
        attribute_value = []
        
        if attribute_type == self.markers["int32"]:
            attribute_value = [struct.unpack('i', self.read_next_bytes(4))[0] for _ in range(attribute_size)]
        elif attribute_type == self.markers["float32"]:
            attribute_value = [struct.unpack('f', self.read_next_bytes(4))[0] for _ in range(attribute_size)]
        
        return attribute_value
    
    def read_next_bytes(self, n):
        if self.reader is None:
            raise ValueError("File not loaded. Please call load() method first.")
        if self.position >= len(self.reader):
            raise EOFError("End of file reached.")
        
        bytes_array = self.reader[self.position:self.position + n]
        self.position += n
        return bytes_array
    
    def read_next_byte(self):
        return self.read_next_bytes(1)[0]

class HoudiniPointCacheSaverBJSON:
    def __init__(self, data, file_path):
        self.data = data
        self.file_path = file_path
        self.buffer = bytearray()

        # Marker definitions
        self.MarkerTypeChar = ord(b'c')
        self.MarkerTypeInt8 = ord(b'b')
        self.MarkerTypeUInt8 = ord(b'B')
        self.MarkerTypeBool = ord(b'?')
        self.MarkerTypeInt16 = ord(b'h')
        self.MarkerTypeUInt16 = ord(b'H')
        self.MarkerTypeInt32 = ord(b'l')
        self.MarkerTypeUInt32 = ord(b'L')
        self.MarkerTypeInt64 = ord(b'q')
        self.MarkerTypeUInt64 = ord(b'Q')
        self.MarkerTypeFloat32 = ord(b'f')
        self.MarkerTypeFloat64 = ord(b'd')
        self.MarkerTypeString = ord(b's')
        self.MarkerObjectStart = ord(b'{')
        self.MarkerObjectEnd = ord(b'}')
        self.MarkerArrayStart = ord(b'[')
        self.MarkerArrayEnd = ord(b']')

    def save(self):
        self.write_marker(self.MarkerObjectStart)
        self.write_object(self.data)
        self.write_marker(self.MarkerObjectEnd)

        with open(self.file_path, 'wb') as file:
            file.write(self.buffer)

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

def convert_file(input_path):
    base, ext = os.path.splitext(input_path)
    output_path = base + (".hbjson" if ext == ".json" else ".json")

    if ext == ".json":
        with open(input_path, 'r') as file:
            data = json.load(file)
        saver = HoudiniPointCacheSaverBJSON(data, output_path)
        saver.save()
    elif ext == ".hbjson":
        loader = HoudiniPointCacheLoaderBJSON(input_path)
        data = loader.load()
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Unsupported file extension: {ext}")
        return

    print(f"Converted {input_path} to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python converter.py <file_path>")
    else:
        convert_file(sys.argv[1])