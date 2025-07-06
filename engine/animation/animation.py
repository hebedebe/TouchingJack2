import pygame

DEFAULT_FPS = 1/24

class Frame:
    def __init__(self, surf):
        self.surface: pygame.Surface = surf

class Animation:
    def __init__(self, frames=[], frame_time = DEFAULT_FPS):
        self.frames: Frame = [Frame(frame) for frame in frames]
        self.frame_time = frame_time

    @property
    def numFrames(self):
        return len(self.frames)