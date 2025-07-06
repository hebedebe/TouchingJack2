from .default_vert import VERT
from ...core.rendering.shader import Shader
from ...core.game import Game

FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D screen_texture;
uniform float cylinder_radius = 1.0;
uniform float field_of_view = 90.0;

void main() {
    // Convert UV coordinates to centered coordinates [-1, 1]
    vec2 centered_uv = (uv - 0.5) * 2.0;
    
    // Calculate the angle that would create the desired warping effect
    float max_angle = radians(field_of_view * 0.5);
    
    // Apply reverse cylindrical mapping - compress from planar to cylindrical
    // This creates barrel distortion where edges get magnified
    float theta = atan(centered_uv.x * tan(max_angle));
    float corrected_x = theta / max_angle;
    float corrected_y = centered_uv.y * cos(theta);
    
    // Convert back to UV space [0, 1]
    vec2 corrected_uv = (vec2(corrected_x, corrected_y) + 1.0) * 0.5;
    
    // Check if the corrected UV is within bounds
    if (corrected_uv.x >= 0.0 && corrected_uv.x <= 1.0 && 
        corrected_uv.y >= 0.0 && corrected_uv.y <= 1.0) {
        fragColor = texture(screen_texture, corrected_uv);
    } else {
        // Black for out-of-bounds areas
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
"""

cylindrical_undo_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="cylindrical_undo")
