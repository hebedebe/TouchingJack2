#Library imports
import pygame
import moderngl
import time
import numpy as np

# Local imports
from .singleton import singleton
from .rendering.shader import Shader, DEFAULT_VERT, DEFAULT_FRAG

# UI Compositing shader for efficient UI rendering
UI_COMPOSITE_FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D scene_texture;  // Post-processed scene
uniform sampler2D ui_texture;     // UI layer

void main() {
    vec4 scene_color = texture(scene_texture, uv);
    vec4 ui_color = texture(ui_texture, uv);
    
    // Alpha blend UI over scene
    fragColor = mix(scene_color, ui_color, ui_color.a);
}
"""

@singleton
class Game:
    def __init__(self, width=1280, height=720, title="OpenGL Game", fullscreen=False):
        print("Initializing Game...")

        pygame.init()
        self.flags = pygame.OPENGL | pygame.DOUBLEBUF | (pygame.FULLSCREEN if fullscreen else 0)
        pygame.display.set_mode((width, height), self.flags)
        pygame.display.set_caption(title)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self.clear_colour = (0, 0, 0, 255)

        self.clock = pygame.time.Clock()
        self.running = True
        self.width = width
        self.height = height
        self.last_time = time.time()
        self.delta_time = 0.1
        
        # 🆕 Performance settings
        self.use_efficient_ui = True  # Toggle between efficient and legacy UI rendering

        self.scenes = {}
        self.current_scene = None
        self.scene_stack = []

        self.init_framebuffers()
        self.init_fullscreen_quad()
        self.shaders = {}
        self.postprocess_chain = []  # 🆕 List of Shader objects in order
        
        self.buffer = pygame.Surface((width, height), pygame.SRCALPHA)

        self.init_default_shader()  # Initialize the default shader

    def quit(self):
        """Quit the game and clean up resources."""
        self.running = False

    def set_fullscreen(self, fullscreen: bool):
        """Toggle fullscreen mode."""
        if fullscreen:
            self.flags |= pygame.FULLSCREEN
        else:
            self.flags &= ~pygame.FULLSCREEN
        pygame.display.set_mode((self.width, self.height), self.flags)
        self.ctx.viewport = (0, 0, self.width, self.height)
        # Reinitialize the buffer to match the new resolution
        self.buffer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Clear VAO cache since framebuffers changed
        self.quad_vao_cache.clear()
        print(f"Fullscreen mode set to {'on' if fullscreen else 'off'}.")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.flags & pygame.FULLSCREEN:
            self.set_fullscreen(False)
        else:
            self.set_fullscreen(True)
        # Debugging: Print current flags
        print(f"Current display flags: {self.flags}")

    def toggle_ui_rendering_mode(self):
        """Toggle between efficient GPU-based UI rendering and legacy CPU-based rendering."""
        self.use_efficient_ui = not self.use_efficient_ui
        mode = "Efficient GPU-based" if self.use_efficient_ui else "Legacy CPU-based"
        print(f"UI rendering mode switched to: {mode}")
        return self.use_efficient_ui

#region OpenGL

    def init_framebuffers(self):
        self.main_color = self.ctx.texture((self.width, self.height), components=4)
        self.main_depth = self.ctx.depth_renderbuffer((self.width, self.height))
        self.scene_fbo = self.ctx.framebuffer(color_attachments=[self.main_color], depth_attachment=self.main_depth)

        # 🆕 ping-pong FBOs for post-processing
        self.ping_tex = self.ctx.texture((self.width, self.height), components=4)
        self.pong_tex = self.ctx.texture((self.width, self.height), components=4)
        self.ping_fbo = self.ctx.framebuffer(color_attachments=[self.ping_tex])
        self.pong_fbo = self.ctx.framebuffer(color_attachments=[self.pong_tex])
        
        # 🆕 UI framebuffer for efficient UI rendering
        self.ui_color = self.ctx.texture((self.width, self.height), components=4)
        self.ui_fbo = self.ctx.framebuffer(color_attachments=[self.ui_color])

    def init_fullscreen_quad(self):
        quad = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
            -1.0,  1.0,
             1.0, -1.0,
             1.0,  1.0,
        ], dtype='f4')
        self.quad_vbo = self.ctx.buffer(quad.tobytes())
        self.quad_vao_cache = {}  # 🆕 Cache VAOs per shader

    def get_quad_vao(self, shader):
        if shader.name not in self.quad_vao_cache:
            vao = self.ctx.simple_vertex_array(shader.program, self.quad_vbo, 'in_position')
            self.quad_vao_cache[shader.name] = vao
        return self.quad_vao_cache[shader.name]

    def load_shader(self, name, vert, frag):
        shader = Shader(vert, frag, name)
        self.shaders[name] = shader
        return shader
    
    def init_default_shader(self):
        self.load_shader('default', DEFAULT_VERT, DEFAULT_FRAG)
        self.load_shader('ui_composite', DEFAULT_VERT, UI_COMPOSITE_FRAG)  # 🆕 UI compositing shader

        self.add_postprocess_shader(self.get_shader('default'))  # Add default shader to post-process chain

    def add_postprocess_shader(self, shader: Shader):
        if shader in self.postprocess_chain:
            print(f"Prevented duplicate shader addition of shader '{shader.name}'.")
            return
        self.postprocess_chain.append(shader)

    def remove_postprocess_shader(self, shader: Shader):
        """Remove a shader from the post-process chain."""
        if shader in self.postprocess_chain:
            self.postprocess_chain.remove(shader)
        else:
            print(f"Shader '{shader.name}' not found in post-process chain.")

    def get_shader(self, name):
        return self.shaders.get(name)

#endregion

#region Scene Management
    def add_scene(self, scene):
        self.scenes[scene.name] = scene
        print(f"Scene '{scene.name}' added.")

    def remove_scene(self, scene_name):
        """Remove a scene by name."""
        if scene_name in self.scenes:
            del self.scenes[scene_name]
        else:
            raise ValueError(f"Scene '{scene_name}' not found.")

    def push_scene(self, scene_name):
        if self.current_scene:
            self.current_scene.on_pause()
        self.current_scene = self.scenes[scene_name]
        self.current_scene.on_enter()
        self.scene_stack.append(self.current_scene)

    def pop_scene(self):
        if not self.scene_stack:
            raise ValueError("No scenes to pop.")
        self.current_scene.on_exit()
        self.scene_stack.pop()
        if self.scene_stack:
            self.current_scene = self.scene_stack[-1]
            self.current_scene.on_resume()
        else:
            self.current_scene = None

    def load_scene(self, scene_name):
        self.scene_stack.clear()  # Clear stack before loading new scene
        if self.current_scene:
            self.current_scene.on_exit()
        self.current_scene = type(self.scenes[scene_name])()
        self.current_scene.on_enter()

# endregion

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.width, self.height = event.size
            pygame.display.set_mode((self.width, self.height), self.flags)
            self.ctx.viewport = (0, 0, self.width, self.height)
            self.init_framebuffers()
            # Reinitialize the buffer to match the new resolution
            self.buffer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            # Clear VAO cache since shaders might need re-binding
            self.quad_vao_cache.clear()
            # Debugging: Print new dimensions
            print(f"Resolution changed: {self.width}x{self.height}")
        elif self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)
            self.current_scene.phys_update(dt)
            self.current_scene.late_update(dt)

    def render_scene(self):
        self.current_scene.render() if self.current_scene else None

    def render_ui(self):
        """Render UI elements to separate UI framebuffer."""
        if self.current_scene:
            self.current_scene.render_ui()
            
    def render_ui_to_texture(self):
        """Render UI to the UI framebuffer efficiently."""
        # Clear UI framebuffer with transparent
        self.ui_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)  # Transparent clear
        
        # Create temporary pygame surface for UI
        ui_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ui_surface.fill((0, 0, 0, 0))  # Clear with transparent
        
        # Render UI to the surface (this is the only pygame rendering)
        if self.current_scene:
            # Temporarily set buffer to UI surface for UI rendering
            old_buffer = self.buffer
            self.buffer = ui_surface
            self.current_scene.render_ui()
            self.buffer = old_buffer
        
        # Upload UI surface to texture (single GPU upload)
        ui_data = pygame.image.tobytes(ui_surface, 'RGBA', True)
        self.ui_color.write(ui_data)

    def render_legacy(self):
        """Legacy rendering method (resource-intensive) for performance comparison."""
        # 🧱 Step 1: Draw to scene framebuffer
        self.scene_fbo.use()
        self.buffer.fill(self.clear_colour)  # Clear buffer with black
        self.render_scene()

        buffer_data = pygame.image.tobytes(self.buffer, 'RGBA', True)
        self.main_color.write(buffer_data)

        # 🧱 Step 2: Postprocess chain - always render to textures, never directly to screen
        src_tex = self.main_color
        for i, _shader in enumerate(self.postprocess_chain):
            shader = _shader.get()
            
            # Choose destination framebuffer (ping-pong between textures)
            dst_fbo = self.ping_fbo if i % 2 == 0 else self.pong_fbo
            dst_fbo.use()

            shader.program['screen_texture'].value = 0
            src_tex.use(location=0)

            vao = self.get_quad_vao(shader)
            vao.render()

            # Next input is current output
            src_tex = self.ping_tex if i % 2 == 0 else self.pong_tex

        # 🧱 Step 3: Render UI elements on top of post-processed result (EXPENSIVE!)
        # Read back the final post-processed result to the pygame buffer
        final_data = src_tex.read()
        # Convert from bytes to pygame surface
        final_surface = pygame.image.frombuffer(final_data, (self.width, self.height), 'RGBA')
        final_surface = pygame.transform.flip(final_surface, False, True)  # Flip vertically
        self.buffer.blit(final_surface, (0, 0))
        
        # Render UI on top
        self.render_ui()
        
        # 🧱 Step 4: Final composite to screen (MORE EXPENSIVE!)
        buffer_data = pygame.image.tobytes(self.buffer, 'RGBA', True)
        screen_texture = self.ctx.texture((self.width, self.height), components=4)
        screen_texture.write(buffer_data)
        
        self.ctx.screen.use()
        default_shader = self.get_shader('default').get()
        default_shader.program['screen_texture'].value = 0
        screen_texture.use(location=0)
        
        vao = self.get_quad_vao(self.get_shader('default'))
        vao.render()
        
        screen_texture.release()

    def render(self):
        """Main render method - uses efficient or legacy rendering based on toggle."""
        if self.use_efficient_ui:
            self.render_efficient()
        else:
            self.render_legacy()
            
    def render_efficient(self):
        """Efficient GPU-only rendering method."""
        # 🧱 Step 1: Render scene to framebuffer
        self.scene_fbo.use()
        self.buffer.fill(self.clear_colour)  # Clear buffer with black
        self.render_scene()

        # Upload scene to texture
        buffer_data = pygame.image.tobytes(self.buffer, 'RGBA', True)
        self.main_color.write(buffer_data)

        # 🧱 Step 2: Apply post-processing chain (GPU-only)
        src_tex = self.main_color
        for i, _shader in enumerate(self.postprocess_chain):
            shader = _shader.get()
            
            # Choose destination framebuffer (ping-pong between textures)
            dst_fbo = self.ping_fbo if i % 2 == 0 else self.pong_fbo
            dst_fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)  # Clear with black

            shader.program['screen_texture'].value = 0
            src_tex.use(location=0)

            vao = self.get_quad_vao(shader)
            vao.render()

            # Next input is current output
            src_tex = self.ping_tex if i % 2 == 0 else self.pong_tex

        # 🧱 Step 3: Render UI to separate texture
        self.render_ui_to_texture()
        
        # 🧱 Step 4: Composite scene + UI and render to screen (GPU-only)
        self.ctx.screen.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        composite_shader = self.get_shader('ui_composite').get()
        composite_shader.program['scene_texture'].value = 0
        composite_shader.program['ui_texture'].value = 1
        
        # Bind both textures
        src_tex.use(location=0)        # Post-processed scene
        self.ui_color.use(location=1)  # UI layer
        
        vao = self.get_quad_vao(composite_shader)
        vao.render()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.update(self.delta_time)
            self.render()
            pygame.display.flip()
            self.delta_time = min(max(float(self.clock.tick())/1000, 0), 1)

        pygame.quit()
