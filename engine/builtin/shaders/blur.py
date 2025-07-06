from .default_vert import VERT
from ...core.rendering.shader import Shader
from ...core.game import Game

FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D screen_texture;
void main() {
    vec2 offsets[9] = vec2[](
        vec2(-1.0,  1.0), vec2(0.0,  1.0), vec2(1.0,  1.0),
        vec2(-1.0,  0.0), vec2(0.0,  0.0), vec2(1.0,  0.0),
        vec2(-1.0, -1.0), vec2(0.0, -1.0), vec2(1.0, -1.0)
    );
    float kernel[9] = float[](
        1.0/16.0, 2.0/16.0, 1.0/16.0,
        2.0/16.0, 4.0/16.0, 2.0/16.0,
        1.0/16.0, 2.0/16.0, 1.0/16.0
    );
    vec3 col = vec3(0.0);
    for (int i = 0; i < 9; i++) {
        col += texture(screen_texture, uv + offsets[i] * 0.005).rgb * kernel[i];
    }
    fragColor = vec4(col, 1.0);
}
"""

blur_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="blur")
