bl_info = {
    "name": "BlockBuster",
    "author": "Stephan Ahlf",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "Topbar (Main Menu)",
    "description": "BlockBuster is a Blender addon that allows you to quickly and easily inspect the size of your Blender datablocks, including meshes, textures, materials, and more. With BlockBuster, you can identify and optimize the largest datablocks in your scene to improve performance and reduce memory usage.",
    "warning": "",
    "doc_url": "",
    "category": "File",
}



import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
import bpy
import math
import os
import sys
from pprint import pprint

# ASCII codes for colors
BLUE = '\x1b[34m'
YELLOW = '\x1b[33m'
CYAN = '\x1b[36m'
RESET = '\x1b[0m'



print("-------------------------------------------------")

# Define a function to list all objects connected to a given datablock
def list_connected_objects(db, visited=None):
    if visited is None:
        visited = set()

    if db.__class__.__name__ == 'Material':
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material == db:
                        print(f"{BLUE} in {obj.name}{RESET}")
    elif db.__class__.__name__ == 'Image':
        for mat in bpy.data.materials:
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == db:
                        print(f"{BLUE} in {mat.name}{RESET}")

        # Check for textures that use this image
        for tex in bpy.data.textures:
            if tex.type == 'IMAGE' and tex.image == db:
                for slot in tex.texture_slots:
                    if slot.material and slot.material not in visited:
                        visited.add(slot.material)
                        print(f"{BLUE} in {slot.material.name}{RESET}")
                        list_connected_objects(slot.material, visited)
    elif db.__class__.__name__ == 'Texture':
        if db.type == 'IMAGE' and db.image:
            for mat in bpy.data.materials:
                if mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image == db.image and mat not in visited:
                            visited.add(mat)
                            print(f"{BLUE} in {mat.name}{RESET}")
                            list_connected_objects(mat, visited)
    elif db.__class__.__name__ == 'Mesh':
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.data == db:
                print(f"{BLUE} in {obj.name}{RESET}")
    elif db.__class__.__name__ == 'Armature':
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj.data == db:
                print(f"{BLUE} in {obj.name}{RESET}")


    
    # Add other checks for other datablock types as needed
    
# Define a function to get the memory size of a datablock
def get_memory_size(db):
    size = sys.getsizeof(db)
    if db.__class__.__name__ in ['Mesh', 'Material']:
        if hasattr(db, 'users'):
            size += sys.getsizeof(db.users)
        if hasattr(db, 'user_map'):
            size += sys.getsizeof(db.user_map)
    return size


# Define a function to get the file size of an image or other file-based datablock
def get_file_size(db):
    if hasattr(db, 'packed_file'):
        if db.__class__.__name__ == 'Image': # check if datablock is an image
            if (hasattr(db.packed_file, 'size')):
                return db.packed_file.size
            else:
                return 0
        else:
            return os.path.getsize(db.packed_file.filepath)
    elif hasattr(db, 'filepath'):
        if os.path.exists(db.filepath):
            if db.__class__.__name__ == 'Image': # check if datablock is an image
                return os.path.getsize(bpy.path.abspath(db.filepath))
            else:
                return os.path.getsize(db.filepath)
        elif hasattr(db, 'library') and os.path.exists(db.library.filepath):
            return os.path.getsize(db.library.filepath)
    return 0


def convert_size(size_bytes):
    """Convert bytes to human-readable form"""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def analyse_blend_file_sizes():
    # Get a list of all datablocks in the scene
    all_datablocks = list(bpy.data.meshes) + list(bpy.data.materials) + \
                     list(bpy.data.textures) + list(bpy.data.images) + list(bpy.data.lights)

    all_datablocks.sort(key=lambda block: get_memory_size(block) + get_file_size(block))

    total_size = 0

    for block in all_datablocks:
        size = get_memory_size(block) + get_file_size(block)
        
        if size > 0:
            total_size += size
            print(f"{CYAN}{block.name} ({block.__class__.__name__}):{RESET} {YELLOW}{convert_size(size)} - {size} bytes{RESET}")
            if size > 100:
                list_connected_objects(block)

    print("-------------------------------------------------")
    print(f"Total size: {convert_size(total_size)}")
    print("-------------------------------------------------")

        

def add_object(self, context):
    analyse_blend_file_sizes()


class CheckFileVolumeOperator(Operator, AddObjectHelper):
    bl_idname = "object.check_file_volume"
    bl_label = "Check File Volume"
    bl_description = "Check the volume of the selected file"

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):
        add_object(self, context)
        self.report({ 'INFO' }, 'Check the Blender System Console!')
        return {'FINISHED'}


# Registration

        

def add_check_file_volume_button(self, context):
    self.layout.operator(
        CheckFileVolumeOperator.bl_idname,
        text="",
        icon='FILE_VOLUME')

def register():
    bpy.utils.register_class(CheckFileVolumeOperator)
    bpy.types.TOPBAR_MT_editor_menus.append(add_check_file_volume_button)


def unregister():
    bpy.utils.unregister_class(CheckFileVolumeOperator)
    bpy.types.TOPBAR_MT_editor_menus.remove(add_check_file_volume_button)


if __name__ == "__main__":
    register()
