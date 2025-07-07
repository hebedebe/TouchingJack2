#Library imports
import pygame
import sys
import time

# Core engine imports
from engine.core.game import Game
from engine.core.asset_manager import AssetManager

# Performance optimization imports
from engine.core.performance.memory_manager import get_memory_manager
from engine.core.performance.cache_manager import get_cache_manager
from engine.core.performance.sprite_cache import get_sprite_cache

# Builtin engine imports
from engine.builtin.shaders import chromatic_aberration, vignette_shader

# Local scene imports
from jumpscare_garfield import JumpscareGarfieldScene
from main_menu import MainMenuScene
from game import GameScene
from nosleep import NoSleepScene
from jumpscare import JumpscareScene
from gameover import GameOverScene
from win import WinScene

def optimize_game_startup():
    """Initialize and optimize game systems for maximum performance"""
    print("Initializing performance optimizations...")
    
    # Initialize performance managers
    memory_manager = get_memory_manager()
    cache_manager = get_cache_manager()
    sprite_cache = get_sprite_cache()
    
    # Apply game-specific optimizations
    memory_manager.optimize_for_game()
    
    # Create performance-optimized caches
    cache_manager.create_cache("game_sprites", max_size=1000, default_ttl=600.0)
    cache_manager.create_cache("ui_elements", max_size=500, default_ttl=300.0)
    cache_manager.create_cache("audio_clips", max_size=200, default_ttl=1200.0)
    
    print("Performance optimizations initialized successfully!")
    
    # Try to import Cython optimizations if available
    try:
        from engine.core.performance.fast_math_c import fast_distance, fast_normalize
        print("Cython optimizations loaded - maximum performance mode active!")
    except ImportError:
        print("Cython optimizations not available - using Numba JIT optimizations")
    
def main(): 
    """Run optimized main"""
    print("Starting Touching Jack 2: The Remake - The Sequel (Complete Edition)")
    print("Optimized Edition with Advanced Performance Features")
    
    start_time = time.time()
    
    # Initialize performance optimizations
    optimize_game_startup()
    
    # Create game instance with optimized settings
    game: Game = Game(640, 480, "Touching Jack 2: The Remake - The Sequel (Complete Edition) [OPTIMIZED]")

    # Initialize asset manager with preloading
    asset_manager = AssetManager()
    asset_manager.autoloadAssets()
    asset_manager.setDefaultFont("vcrosdmono")

    # Add post-processing shaders
    game.add_postprocess_shader(vignette_shader)

    # Add all scenes
    game.add_scene(MainMenuScene())
    game.add_scene(GameScene())
    game.add_scene(NoSleepScene())
    game.add_scene(JumpscareScene())
    game.add_scene(JumpscareGarfieldScene())
    game.add_scene(GameOverScene())
    game.add_scene(WinScene())

    # Load initial scene
    game.load_scene("MainMenu")
    
    # Print startup time and performance info
    startup_time = time.time() - start_time
    print(f"Game initialized in {startup_time:.2f} seconds")
    
    # Print performance statistics
    memory_manager = get_memory_manager()
    sprite_cache = get_sprite_cache()
    
    memory_stats = memory_manager.get_performance_stats()
    cache_stats = sprite_cache.get_cache_stats()
    
    print(f"Memory usage: {memory_stats['current_memory_mb']:.1f}MB")
    print(f"Sprite cache initialized with {cache_stats['surface_cache_size']} surfaces")
    print("Starting optimized game loop...")

    # Run the optimized game
    game.run()

if __name__ == "__main__":
    main()
