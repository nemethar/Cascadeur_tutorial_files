import csc
import common.selection_operations as so
from pycsc import data_constants as dc


def command_name():
    return "Rig additional.Fix LookAt constraint"

def command_description():
    return "Fixes selected LookAt constraints, to make the constrained object follow its parent"

def run(scene):
    mv = scene.model_viewer()
    sel_objs = so.selected_obj_ids(scene)

    constraints = [obj_id for obj_id in sel_objs if 'Constraint' in mv.get_object_name(obj_id)]
    if len(constraints) == 0:
        scene.error('No constraints found in the selection')
        return

    for constraint_obj_id in constraints:
        def mod(model, update, scene_updater):
            constraint_obj = update.get_object_by_id(constraint_obj_id)
            constrained_obj = constraint_obj.root_group().output('Active').connected_attributes()[0].node()
            constrained_obj.input('Rotation').disconnect()
            constrained_obj.input('Enforce Global').disconnect()
            constrained_obj.parent_group().constant_settings().output('false').connect(constrained_obj.input('Enforce Global'))

            const_active_input = constrained_obj.add_input('LookAt Constraint Active')
            constraint_obj.output('Active').connect(const_active_input)
            const_rot_input = constrained_obj.add_input('LookAt Constraint Rotation')
            constraint_obj.output('Constrained Global Rotation').connect(const_rot_input)

            local_group = constrained_obj.node_deep('Local')
            localgrp_active_input = local_group.add_input('LookAt Constraint Active')
            const_active_input.other_side().connect(localgrp_active_input)
            localgrp_rot_input = local_group.add_input('LookAt Constraint Rotation')
            const_rot_input.other_side().connect(localgrp_rot_input)

            lookat_rot_func = local_group.create_regular_function('LookAt Rotation', 'MultiplyInversedRotation')
            local_group.input('Parent Rotation').other_side().connect(lookat_rot_func.input('first'))

            lookat_rot_node = local_group.create_regular_data('LookAt_Rot', dc.zero_rot, csc.model.DataMode.Animation)
            localgrp_rot_input.other_side().connect(lookat_rot_node.input())
            lookat_rot_node.output().connect(lookat_rot_func.input('second'))

            andnot_node = local_group.create_setting_function('AndNot', 'AndNot')
            local_group.input('Global->Local').other_side().connect(andnot_node.input('a'))
            localgrp_active_input.other_side().connect(andnot_node.input('b'))
            local_rot_func = local_group.node_deep('Local Rotation Func')
            local_rot_func.input('activity').disconnect()
            andnot_node.output('out').connect(local_rot_func.input('activity'))
            localgrp_active_input.other_side().connect(lookat_rot_func.input('activity'))
            local_rot_node = local_group.node_deep('Local Rotation')
            lookat_rot_func.output('result').connect(local_rot_node.input())

            scene_updater.generate_update()

        scene.modify_update(command_name(), mod)

    scene.success("Fixed the selected constraints!")
