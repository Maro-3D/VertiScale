bl_info = {
    "name": "Scale Object to Match Vertex Distance",
    "blender": (4, 0, 0),
    "category": "Object",
    "author": "Your Name",
    "version": (1, 1, 2),
    "description": "Uniformly scale an object based on the distance between two selected vertices."
}

import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty

class OBJECT_OT_scale_to_vertex_distance(bpy.types.Operator):
    """Scale Object to Match Vertex Distance"""
    bl_idname = "object.scale_to_vertex_distance"
    bl_label = "Scale to Vertex Distance"
    bl_options = {'REGISTER', 'UNDO'}

    target_distance: FloatProperty(
        name="Target Distance",
        description="Desired distance between the two vertices",
        subtype='DISTANCE',
        default=1.0,
        min=0  # This prevents the property from going negative.
    )

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            self.report({'ERROR'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode")
            return {'CANCELLED'}

        # Get updated bmesh data and ensure changes are updated.
        bm = bmesh.from_edit_mesh(obj.data)
        bmesh.update_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) != 2:
            self.report({'ERROR'}, "Select exactly two vertices")
            return {'CANCELLED'}

        # Convert vertex coordinates from local to world space.
        v1_world = obj.matrix_world @ selected_verts[0].co
        v2_world = obj.matrix_world @ selected_verts[1].co
        current_distance = (v1_world - v2_world).length

        if current_distance == 0:
            self.report({'ERROR'}, "Selected vertices are at the same location")
            return {'CANCELLED'}

        # Clamp the target distance: if target is 0, warn and use a small positive value.
        min_target_distance = 1e-6
        if self.target_distance <= 0:
            self.report({'WARNING'}, f"Target distance cannot be 0; using minimum value {min_target_distance:.6f}")
            effective_target_distance = min_target_distance
        else:
            effective_target_distance = self.target_distance

        # Calculate the uniform scale factor.
        scale_factor = effective_target_distance / current_distance

        # Avoid scaling if no change is needed.
        if abs(scale_factor - 1.0) < 1e-6:
            self.report({'INFO'}, "No scaling needed")
            return {'FINISHED'}

        # Compute the pivot as the midpoint between the two selected vertices.
        pivot = (v1_world + v2_world) * 0.5

        # Compute the new world location so that the pivot remains fixed.
        old_world_loc = obj.matrix_world.to_translation()
        new_world_loc = pivot + (old_world_loc - pivot) * scale_factor

        # Apply the uniform scaling.
        obj.scale *= scale_factor

        # Update object location, converting to parent space if necessary.
        if obj.parent:
            obj.location = obj.parent.matrix_world.inverted() @ new_world_loc
        else:
            obj.location = new_world_loc

        self.report({'INFO'}, "Object scaled successfully")
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            self.report({'ERROR'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bmesh.update_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) != 2:
            self.report({'ERROR'}, "Select exactly two vertices")
            return {'CANCELLED'}

        # Calculate the current world-space distance between the selected vertices.
        v1_world = obj.matrix_world @ selected_verts[0].co
        v2_world = obj.matrix_world @ selected_verts[1].co
        current_distance = (v1_world - v2_world).length

        # Pre-fill the dialog's field with the current measured distance.
        self.target_distance = current_distance
        return context.window_manager.invoke_props_dialog(self)

# Integrate the operator into the Edit Mode right-click context menu.
def menu_draw(self, context):
    self.layout.operator(OBJECT_OT_scale_to_vertex_distance.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_scale_to_vertex_distance)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_draw)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_draw)
    bpy.utils.unregister_class(OBJECT_OT_scale_to_vertex_distance)

if __name__ == "__main__":
    register()
