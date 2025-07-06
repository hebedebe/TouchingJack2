import pygame
from typing import Optional

from ...core.world.component import Component
from ...core.asset_manager import AssetManager

class AudioComponent(Component):
    """
    AudioComponent handles audio playback for actors.
    It can play sound effects and music tracks using asset references.
    """
    
    # Exclude runtime audio state from serialization
    __serialization_exclude__ = ["_sound_object", "_channel"]
    
    def __init__(self, sound_name: str = None, volume: float = 1.0, loop: bool = False):
        super().__init__()
        
        # Asset reference
        self.sound_name: Optional[str] = sound_name
        
        # Audio properties
        self.volume: float = max(0.0, min(1.0, volume))  # Clamp between 0.0 and 1.0
        self.loop: bool = loop
        self.autoplay: bool = False  # Whether to start playing when component starts
        
        # Runtime state
        self._sound_object: Optional[pygame.mixer.Sound] = None
        self._channel: Optional[pygame.mixer.Channel] = None
        self.is_playing: bool = False
        
    def set_sound(self, sound_name: str) -> None:
        """Set the sound asset name."""
        if self.sound_name != sound_name:
            self.stop()  # Stop current sound if playing
            self.sound_name = sound_name
            self._sound_object = None  # Reset cached sound object
            
    def set_volume(self, volume: float) -> None:
        """Set the volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self._sound_object:
            self._sound_object.set_volume(self.volume)
        
    def _get_sound_object(self) -> Optional[pygame.mixer.Sound]:
        """Get the sound object from the asset manager."""
        if not self.sound_name:
            return None
            
        # Return cached sound if available
        if self._sound_object:
            return self._sound_object
            
        # Try to get from asset manager cache first
        asset_manager = AssetManager()
        sound = asset_manager.getSound(self.sound_name)
        
        if not sound:
            # Load the sound if not cached
            sound = asset_manager.loadSound(self.sound_name)
            
        if sound:
            # Cache the sound object and set volume
            self._sound_object = sound
            self._sound_object.set_volume(self.volume)
            
        return self._sound_object

    def play(self, loops: int = None) -> bool:
        """
        Play the audio file.
        
        Args:
            loops: Number of loops (-1 for infinite, None to use component's loop setting)
            
        Returns:
            True if playback started successfully, False otherwise
        """
        if not self.sound_name:
            return False
            
        sound = self._get_sound_object()
        if not sound:
            return False
            
        # Stop current playback if any
        self.stop()
        
        # Determine loop count
        if loops is None:
            loops = -1 if self.loop else 0
            
        try:
            # Play the sound and get the channel
            self._channel = sound.play(loops=loops)
            if self._channel:
                self.is_playing = True
                return True
        except pygame.error as e:
            print(f"Error playing sound {self.sound_name}: {e}")
            
        return False

    def stop(self) -> None:
        """Stop the audio playback."""
        if self.is_playing and self._channel:
            self._channel.stop()
            self._channel = None
            self.is_playing = False

    def pause(self) -> None:
        """Pause the audio playback."""
        if self.is_playing and self._channel:
            self._channel.pause()

    def unpause(self) -> None:
        """Resume the audio playback."""
        if self.is_playing and self._channel:
            self._channel.unpause()
            
    def is_sound_playing(self) -> bool:
        """Check if the sound is currently playing."""
        if self._channel:
            playing = self._channel.get_busy()
            if not playing:
                # Update our state if the sound finished naturally
                self.is_playing = False
                self._channel = None
            return playing
        return False
        
    def get_position(self) -> int:
        """Get the current playback position in milliseconds."""
        if self._channel:
            return self._channel.get_pos()
        return 0
        
    def set_position(self, pos: int) -> None:
        """Set the playback position (if supported by the sound format)."""
        if self._channel:
            self._channel.set_pos(pos)
            
    def fade_out(self, time_ms: int) -> None:
        """Fade out the sound over the given time."""
        if self.is_playing and self._channel:
            self._channel.fadeout(time_ms)
            self.is_playing = False
            self._channel = None
            
    def start(self) -> None:
        """Initialize the audio component when attached to an actor."""
        super().start()
        
        # Preload the sound if specified
        if self.sound_name:
            self._get_sound_object()
            
        # Autoplay if enabled
        if self.autoplay:
            self.play()
            
    def update(self, dt: float) -> None:
        """Update the audio component."""
        super().update(dt)
        
        # Update playing state
        if self.is_playing:
            self.is_sound_playing()  # This will update our state automatically
            
    def serialize(self) -> dict:
        """Serialize the audio component data."""
        data = super().serialize()
        # Runtime state like is_playing is not serialized intentionally
        return data