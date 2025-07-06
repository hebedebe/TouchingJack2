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
    vec3 sepia = vec3(0.393, 0.769, 0.189) * col.r +
                 vec3(0.349, 0.686, 0.168) * col.g +
                 vec3(0.272, 0.534, 0.131) * col.b;
    fragColor = vec4(sepia, 1.0);
}
"""

sepia_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="sepia")
