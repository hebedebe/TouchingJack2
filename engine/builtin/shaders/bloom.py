from .default_vert import VERT
from ...core.rendering.shader import Shader
from ...core.game import Game

FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D screen_texture;
void main() {
    vec3 col = texture(screen_texture, uv).rgb;
    vec3 bloom = col * vec3(1.2, 1.2, 1.2); // Brighten colors
    fragColor = vec4(bloom, 1.0);
}
"""

bloom_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="bloom")
