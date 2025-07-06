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
    fragColor = vec4(1.0 - col, 1.0);
}
"""

invert_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="invert")
