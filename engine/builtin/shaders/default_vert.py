VERT = """
#version 330

in vec2 in_position;
out vec2 uv;

void main() {
    // Convert from clip space [-1, 1] to UV space [0, 1]
    uv = (in_position + 1.0) * 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""