from .default_vert import VERT
from ...core.rendering.shader import Shader
from ...core.game import Game

FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D screen_texture;
void main() {
    vec3 col;
    float aberration_strength = 0.002; // Adjust this value to control the strength of the chromatic aberration
    col.r = texture(screen_texture, uv + vec2(aberration_strength, 0.0)).r;
    col.g = texture(screen_texture, uv).g;
    col.b = texture(screen_texture, uv - vec2(aberration_strength, 0.0)).b;
    fragColor = vec4(col, 1.0);
}
"""

chromatic_aberration_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="chromatic_aberration")
