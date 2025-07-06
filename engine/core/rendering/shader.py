DEFAULT_VERT = """
#version 330

in vec2 in_position;
out vec2 uv;

void main() {
    // Convert from clip space [-1, 1] to UV space [0, 1]
    uv = (in_position + 1.0) * 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

DEFAULT_FRAG = """
#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D screen_texture;
void main() {
    fragColor = texture(screen_texture, uv);
}
"""

class Shader:
    def __init__(self, vertex_src, fragment_src, name="unnamed"):
        self.vertex_src = vertex_src
        self.fragment_src = fragment_src
        
        self.name = name

        self.initialized = False

    def init(self):
        if self.initialized: return
        from ..game import Game
        try:
            self.program = Game().ctx.program(vertex_shader=self.vertex_src, fragment_shader=self.fragment_src)
            self.initialized = True
        except Exception as e:
            print(f"Failed to compile shader {self.name}:\n{e}")

    def get(self):
        self.init()
        return self

    def set_uniform(self, name, value):
        if name in self.program:
            self.program[name].value = value
        else:
            raise KeyError(f"Uniform '{name}' not found in shader '{self.name}'")
