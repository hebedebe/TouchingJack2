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

    // Use the posterized color
    fragColor = vec4(floor(col * 4.0) / 4.0, 1.0);
}
"""

posterize_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="posterize")