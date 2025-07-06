import pygame
from typing import Callable, Dict, Optional, Set, Any
from engine.core.world.component import Component

class InputComponent(Component):
    """
    InputComponent handles user input for actors.
    It can process keyboard and mouse events with flexible key binding system.
    """
    
    # Exclude callback functions from serialization
    __serialization_exclude__ = ["key_bindings", "mouse_bindings", "_pressed_keys", "_pressed_mouse"]
    
    def __init__(self):
        super().__init__()
        
        # Input bindings (functions can't be serialized, so we exclude them)
        self.key_bindings: Dict[int, Callable] = {}  # pygame key constants -> functions
        self.mouse_bindings: Dict[int, Callable] = {}  # mouse button numbers -> functions
        
        # Key/button states for continuous input
        self._pressed_keys: Set[int] = set()
        self._pressed_mouse: Set[int] = set()
        
        # Input configuration
        self.enabled_keys: bool = True
        self.enabled_mouse: bool = True
        self.consume_events: bool = False  # Whether to consume handled events
        
        # Input modifiers
        self.require_focus: bool = False  # Whether input requires some form of focus
        
    def bind_key(self, key: int, action: Callable, on_press: bool = True, on_release: bool = False) -> None:
        """
        Bind a key to an action.
        
        Args:
            key: pygame key constant (e.g., pygame.K_SPACE)
            action: Function to call when key is pressed/released
            on_press: Whether to call action on key press
            on_release: Whether to call action on key release
        """
        if not callable(action):
            raise ValueError("Action must be callable")
            
        if key not in self.key_bindings:
            self.key_bindings[key] = []
        
        self.key_bindings[key].append({
            'action': action,
            'on_press': on_press,
            'on_release': on_release
        })
        
    def bind_mouse(self, button: int, action: Callable, on_press: bool = True, on_release: bool = False) -> None:
        """
        Bind a mouse button to an action.
        
        Args:
            button: Mouse button number (1=left, 2=middle, 3=right)
            action: Function to call when button is pressed/released
            on_press: Whether to call action on button press
            on_release: Whether to call action on button release
        """
        if not callable(action):
            raise ValueError("Action must be callable")
            
        if button not in self.mouse_bindings:
            self.mouse_bindings[button] = []
            
        self.mouse_bindings[button].append({
            'action': action,
            'on_press': on_press,
            'on_release': on_release
        })
        
    def unbind_key(self, key: int) -> None:
        """Remove all bindings for a key."""
        if key in self.key_bindings:
            del self.key_bindings[key]
            
    def unbind_mouse(self, button: int) -> None:
        """Remove all bindings for a mouse button."""
        if button in self.mouse_bindings:
            del self.mouse_bindings[button]
            
    def clear_bindings(self) -> None:
        """Clear all input bindings."""
        self.key_bindings.clear()
        self.mouse_bindings.clear()
        
    def is_key_pressed(self, key: int) -> bool:
        """Check if a key is currently being held down."""
        return key in self._pressed_keys
        
    def is_mouse_pressed(self, button: int) -> bool:
        """Check if a mouse button is currently being held down."""
        return button in self._pressed_mouse
        
    def get_pressed_keys(self) -> Set[int]:
        """Get all currently pressed keys."""
        return self._pressed_keys.copy()
        
    def get_pressed_mouse_buttons(self) -> Set[int]:
        """Get all currently pressed mouse buttons."""
        return self._pressed_mouse.copy()
        
    def _get_input_manager(self):
        """Get the input manager from the game instance."""
        from engine import Game
        game = Game()
        return game.inputManager
        
    def handle_key_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a keyboard event.
        
        Returns:
            True if the event was handled and consumed, False otherwise
        """
        if not self.enabled_keys or not self.enabled:
            return False
            
        handled = False
        key = event.key
        
        if event.type == pygame.KEYDOWN:
            self._pressed_keys.add(key)
            
            if key in self.key_bindings:
                for binding in self.key_bindings[key]:
                    if binding['on_press']:
                        try:
                            binding['action']()
                            handled = True
                        except Exception as e:
                            print(f"Error in key binding for key {key}: {e}")
                            
        elif event.type == pygame.KEYUP:
            self._pressed_keys.discard(key)
            
            if key in self.key_bindings:
                for binding in self.key_bindings[key]:
                    if binding['on_release']:
                        try:
                            binding['action']()
                            handled = True
                        except Exception as e:
                            print(f"Error in key binding for key {key}: {e}")

        return handled and self.consume_events

    def handle_mouse_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a mouse event.
        
        Returns:
            True if the event was handled and consumed, False otherwise
        """
        if not self.enabled_mouse or not self.enabled:
            return False
            
        handled = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            button = event.button
            self._pressed_mouse.add(button)
            
            if button in self.mouse_bindings:
                for binding in self.mouse_bindings[button]:
                    if binding['on_press']:
                        try:
                            binding['action']()
                            handled = True
                        except Exception as e:
                            print(f"Error in mouse binding for button {button}: {e}")
                            
        elif event.type == pygame.MOUSEBUTTONUP:
            button = event.button
            self._pressed_mouse.discard(button)
            
            if button in self.mouse_bindings:
                for binding in self.mouse_bindings[button]:
                    if binding['on_release']:
                        try:
                            binding['action']()
                            handled = True
                        except Exception as e:
                            print(f"Error in mouse binding for button {button}: {e}")

        return handled and self.consume_events
        
    def update(self, dt: float) -> None:
        """Update the input component."""
        super().update(dt)
        
        # Sync with the global input manager state
        input_manager = self._get_input_manager()
        
        # Update key states based on current input manager state
        all_keys = pygame.key.get_pressed()
        current_pressed = set()
        
        for key_code in range(len(all_keys)):
            if all_keys[key_code]:
                current_pressed.add(key_code)
                
        # Update our tracked state
        self._pressed_keys = current_pressed
        
        # Update mouse button states
        mouse_buttons = pygame.mouse.get_pressed()
        current_mouse = set()
        
        for i, pressed in enumerate(mouse_buttons):
            if pressed:
                current_mouse.add(i + 1)  # pygame uses 0-based, we use 1-based
                
        self._pressed_mouse = current_mouse
        
    def serialize(self) -> dict:
        """Serialize the input component data."""
        # Note: We intentionally don't serialize the bindings since they contain function references
        # Users will need to re-establish bindings after deserialization
        return super().serialize()
        
    # Helper methods for common key bindings
    def bind_movement_keys(self, up_action: Callable, down_action: Callable, 
                          left_action: Callable, right_action: Callable,
                          keys: Dict[str, int] = None) -> None:
        """
        Convenience method to bind movement keys.
        
        Args:
            up_action, down_action, left_action, right_action: Movement functions
            keys: Dictionary with 'up', 'down', 'left', 'right' keys (defaults to WASD)
        """
        if keys is None:
            keys = {
                'up': pygame.K_w,
                'down': pygame.K_s,
                'left': pygame.K_a,
                'right': pygame.K_d
            }
            
        self.bind_key(keys['up'], up_action)
        self.bind_key(keys['down'], down_action)
        self.bind_key(keys['left'], left_action)
        self.bind_key(keys['right'], right_action)
        
    def bind_action_key(self, action: Callable, key: int = pygame.K_SPACE) -> None:
        """Convenience method to bind an action key."""
        self.bind_key(key, action)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame event.
        
        Returns:
            True if the event was handled and consumed, False otherwise
        """
        if not self.enabled:
            return False
            
        # Handle keyboard events
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            return self.handle_key_event(event)
        
        # Handle mouse events
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return self.handle_mouse_event(event)
            
        return False