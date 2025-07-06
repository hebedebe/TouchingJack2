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
    float dist = length(uv - vec2(0.5, 0.5));
    float vignette = smoothstep(0.8, 0.5, dist);
    fragColor = vec4(col * vignette, 1.0);
}
"""

vignette_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="vignette")
