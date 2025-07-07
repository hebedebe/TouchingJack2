"""
High-performance OpenGL batch renderer to reduce draw calls
"""
import moderngl
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import pygame
from dataclasses import dataclass
from enum import Enum

class BlendMode(Enum):
    NORMAL = 0
    ADDITIVE = 1
    MULTIPLY = 2
    SCREEN = 3

@dataclass
class SpriteData:
    """Data for a single sprite in the batch"""
    texture_id: int
    position: Tuple[float, float]
    size: Tuple[float, float]
    rotation: float
    tint: Tuple[float, float, float, float]
    uv_rect: Tuple[float, float, float, float]  # (u1, v1, u2, v2)
    depth: float = 0.0

@dataclass
class RenderBatch:
    """A batch of sprites to render together"""
    texture_id: int
    blend_mode: BlendMode
    sprites: List[SpriteData]
    vertex_data: Optional[np.ndarray] = None

class BatchRenderer:
    """High-performance batch renderer using OpenGL"""
    
    VERTEX_SHADER = """
    #version 330 core
    
    layout (location = 0) in vec2 position;
    layout (location = 1) in vec2 texCoord;
    layout (location = 2) in vec4 color;
    layout (location = 3) in float depth;
    
    uniform mat4 projection;
    uniform mat4 view;
    
    out vec2 fragTexCoord;
    out vec4 fragColor;
    
    void main() {
        gl_Position = projection * view * vec4(position, depth, 1.0);
        fragTexCoord = texCoord;
        fragColor = color;
    }
    """
    
    FRAGMENT_SHADER = """
    #version 330 core
    
    in vec2 fragTexCoord;
    in vec4 fragColor;
    
    uniform sampler2D spriteTexture;
    uniform int blendMode;
    
    out vec4 color;
    
    void main() {
        vec4 texColor = texture(spriteTexture, fragTexCoord);
        
        // Apply tint
        texColor *= fragColor;
        
        // Apply blend mode
        switch(blendMode) {
            case 0: // Normal
                color = texColor;
                break;
            case 1: // Additive
                color = vec4(texColor.rgb, texColor.a);
                break;
            case 2: // Multiply
                color = texColor; // Handled by OpenGL blend state
                break;
            case 3: // Screen
                color = vec4(1.0 - (1.0 - texColor.rgb) * (1.0 - fragColor.rgb), texColor.a);
                break;
            default:
                color = texColor;
        }
    }
    """
    
    def __init__(self, ctx: moderngl.Context, max_sprites_per_batch: int = 10000):
        self.ctx = ctx
        self.max_sprites_per_batch = max_sprites_per_batch
        
        # Shader program
        self.program = ctx.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
        )
        
        # Vertex buffer for quad (will be instanced)
        quad_vertices = np.array([
            # Position    # TexCoord
            -0.5, -0.5,   0.0, 1.0,  # Bottom-left
             0.5, -0.5,   1.0, 1.0,  # Bottom-right
             0.5,  0.5,   1.0, 0.0,  # Top-right
            -0.5,  0.5,   0.0, 0.0   # Top-left
        ], dtype=np.float32)
        
        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        
        self.quad_vbo = ctx.buffer(quad_vertices.tobytes())
        self.quad_ibo = ctx.buffer(indices.tobytes())
        
        # Instance data buffer (position, size, rotation, tint, uv_rect, depth)
        # Each sprite: pos(2) + size(2) + rotation(1) + tint(4) + uv(4) + depth(1) = 14 floats
        self.instance_buffer_size = max_sprites_per_batch * 14 * 4  # 4 bytes per float
        self.instance_vbo = ctx.buffer(reserve=self.instance_buffer_size)
        
        # VAO
        self.vao = ctx.vertex_array(
            self.program,
            [(self.quad_vbo, '2f 2f', 'position', 'texCoord'),
             (self.instance_vbo, '2f 2f 1f 4f 4f 1f/i', 'instancePos', 'instanceSize', 
              'instanceRotation', 'instanceTint', 'instanceUV', 'instanceDepth')],
            self.quad_ibo
        )
        
        # Render batches
        self.batches: List[RenderBatch] = []
        self.current_batch: Optional[RenderBatch] = None
        
        # Texture management
        self.textures: Dict[int, moderngl.Texture] = {}
        self.next_texture_id = 1
        
        # Projection matrix (will be set by renderer)
        self.projection_matrix = np.eye(4, dtype=np.float32)
        self.view_matrix = np.eye(4, dtype=np.float32)
        
        # Statistics
        self.draw_calls = 0
        self.sprites_rendered = 0
        self.batches_rendered = 0
    
    def set_projection_matrix(self, matrix: np.ndarray) -> None:
        """Set projection matrix"""
        self.projection_matrix = matrix.astype(np.float32)
    
    def set_view_matrix(self, matrix: np.ndarray) -> None:
        """Set view matrix"""
        self.view_matrix = matrix.astype(np.float32)
    
    def register_texture(self, surface: pygame.Surface) -> int:
        """Register a pygame surface as an OpenGL texture"""
        texture_data = pygame.image.tobytes(surface, 'RGBA', True)
        texture = self.ctx.texture(surface.get_size(), components=4)
        texture.write(texture_data)
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        texture_id = self.next_texture_id
        self.textures[texture_id] = texture
        self.next_texture_id += 1
        
        return texture_id
    
    def begin_batch(self) -> None:
        """Begin a new frame"""
        self.batches.clear()
        self.current_batch = None
        self.draw_calls = 0
        self.sprites_rendered = 0
        self.batches_rendered = 0
    
    def add_sprite(self, texture_id: int, position: Tuple[float, float], 
                   size: Tuple[float, float], rotation: float = 0.0,
                   tint: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                   uv_rect: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
                   depth: float = 0.0, blend_mode: BlendMode = BlendMode.NORMAL) -> None:
        """Add a sprite to the current batch"""
        
        sprite = SpriteData(texture_id, position, size, rotation, tint, uv_rect, depth)
        
        # Check if we can add to current batch
        if (self.current_batch is None or 
            self.current_batch.texture_id != texture_id or
            self.current_batch.blend_mode != blend_mode or
            len(self.current_batch.sprites) >= self.max_sprites_per_batch):
            
            # Start new batch
            self.current_batch = RenderBatch(texture_id, blend_mode, [])
            self.batches.append(self.current_batch)
        
        self.current_batch.sprites.append(sprite)
    
    def _build_vertex_data(self, batch: RenderBatch) -> np.ndarray:
        """Build vertex data for a batch"""
        sprite_count = len(batch.sprites)
        vertex_data = np.zeros((sprite_count, 14), dtype=np.float32)
        
        for i, sprite in enumerate(batch.sprites):
            vertex_data[i] = [
                sprite.position[0], sprite.position[1],  # position
                sprite.size[0], sprite.size[1],          # size
                sprite.rotation,                         # rotation
                sprite.tint[0], sprite.tint[1], sprite.tint[2], sprite.tint[3],  # tint
                sprite.uv_rect[0], sprite.uv_rect[1], sprite.uv_rect[2], sprite.uv_rect[3],  # uv
                sprite.depth                             # depth
            ]
        
        return vertex_data
    
    def render_batches(self) -> None:
        """Render all batches"""
        if not self.batches:
            return
        
        # Set uniforms
        self.program['projection'].write(self.projection_matrix.tobytes())
        self.program['view'].write(self.view_matrix.tobytes())
        
        # Enable depth testing
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.depth_func = '<='
        
        for batch in self.batches:
            self._render_batch(batch)
        
        self.ctx.disable(moderngl.DEPTH_TEST)
    
    def _render_batch(self, batch: RenderBatch) -> None:
        """Render a single batch"""
        if not batch.sprites:
            return
        
        # Get texture
        texture = self.textures.get(batch.texture_id)
        if not texture:
            return
        
        # Set blend mode
        self._set_blend_mode(batch.blend_mode)
        
        # Build and upload vertex data
        vertex_data = self._build_vertex_data(batch)
        self.instance_vbo.write(vertex_data.tobytes())
        
        # Bind texture
        texture.use(0)
        self.program['spriteTexture'].value = 0
        self.program['blendMode'].value = batch.blend_mode.value
        
        # Render
        self.vao.render(instances=len(batch.sprites))
        
        # Update statistics
        self.draw_calls += 1
        self.sprites_rendered += len(batch.sprites)
        self.batches_rendered += 1
    
    def _set_blend_mode(self, blend_mode: BlendMode) -> None:
        """Set OpenGL blend mode"""
        if blend_mode == BlendMode.NORMAL:
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        elif blend_mode == BlendMode.ADDITIVE:
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        elif blend_mode == BlendMode.MULTIPLY:
            self.ctx.blend_func = (moderngl.DST_COLOR, moderngl.ZERO)
        elif blend_mode == BlendMode.SCREEN:
            self.ctx.blend_func = (moderngl.ONE_MINUS_DST_COLOR, moderngl.ONE)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rendering statistics"""
        return {
            'draw_calls': self.draw_calls,
            'sprites_rendered': self.sprites_rendered,
            'batches_rendered': self.batches_rendered,
            'textures_loaded': len(self.textures)
        }
    
    def cleanup(self) -> None:
        """Clean up resources"""
        for texture in self.textures.values():
            texture.release()
        self.textures.clear()
        
        if hasattr(self, 'vao'):
            self.vao.release()
        if hasattr(self, 'quad_vbo'):
            self.quad_vbo.release()
        if hasattr(self, 'quad_ibo'):
            self.quad_ibo.release()
        if hasattr(self, 'instance_vbo'):
            self.instance_vbo.release()
        if hasattr(self, 'program'):
            self.program.release()
