# A starting scene for a 3D shot (Blender 5.2): a chrome torus that spins for 1 s, lit by an HDRI, on a
# transparent background. Copy it to the film folder as 3d/shot.py, change the object and the motion, and run
# it from the film folder:  blender -b --factory-startup -P 3d/shot.py -a   (reference/engine-html.md)
import bpy, json, os
FPS, FRAMES, W, H = 60, 60, 1280, 720             # the film's fps and size
OUT = os.path.abspath('footage/torus')            # 0001.png, 0002.png... and clip.json

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
cycles = bpy.context.preferences.addons['cycles'].preferences
cycles.compute_device_type = 'METAL'
cycles.get_devices()
scene.render.engine, scene.cycles.device = 'CYCLES', 'GPU'
scene.cycles.samples, scene.cycles.seed = 64, 7
scene.render.fps, scene.frame_start, scene.frame_end = FPS, 1, FRAMES
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.filepath = OUT + '/'
scene.render.film_transparent = True              # the HDRI lights the object; the film's own background shows through

scene.world = bpy.data.worlds.new('hdri')
env = scene.world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(os.path.abspath('3d/studio_small_09_1k.hdr'))
scene.world.node_tree.links.new(env.outputs['Color'], scene.world.node_tree.nodes['Background'].inputs['Color'])

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.35, major_segments=96, minor_segments=32)
bpy.ops.object.shade_smooth()
torus = bpy.context.object
gloss = bpy.data.materials.new('gloss')
bsdf = gloss.node_tree.nodes['Principled BSDF']
bsdf.inputs['Metallic'].default_value, bsdf.inputs['Roughness'].default_value = 1, 0.12
torus.data.materials.append(gloss)
torus.rotation_euler.x = 1.1
# Motion as a function of the frame (a simple driver expression runs with scripts disabled).
torus.driver_add('rotation_euler', 2).driver.expression = f'frame / {FPS} * 1.5'

bpy.ops.object.camera_add(location=(0, -8, 0), rotation=(1.5708, 0, 0))
scene.camera = bpy.context.object

os.makedirs(OUT, exist_ok=True)
json.dump({'fps': FPS, 'frames': FRAMES, 'seconds': FRAMES / FPS, 'size': [W, H], 'ext': 'png'}, open(OUT + '/clip.json', 'w'))
