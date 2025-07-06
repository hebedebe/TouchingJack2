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
    float gray = dot(col, vec3(0.299, 0.587, 0.114));
    
    // Use the grayscale value
    fragColor = vec4(gray, gray, gray, 1.0);
}
"""

greyscale_shader = Shader(vertex_src=VERT, fragment_src=FRAG, name="greyscale")