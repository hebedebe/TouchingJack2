"""
Script to build the executable using PyInstaller with proper ModernGL support
Run this script to create the executable instead of using auto-py-to-exe
"""
import subprocess
import sys
import os

def build_exe():
    """Build the executable with proper hidden imports"""
    
    # Define the PyInstaller command with all necessary options
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window (remove this if you want to see console output)
        "--name", "Touching Jack 2",  # Name of the executable
        "--icon", "assets/images/jack_outside.jpg" if os.path.exists("assets/images/jack_outside.jpg") else None,

        # Hidden imports for ModernGL and dependencies
        "--hidden-import", "glcontext",
        "--hidden-import", "moderngl",
        "--hidden-import", "moderngl.context",
        "--hidden-import", "OpenGL",
        "--hidden-import", "OpenGL.GL",
        "--hidden-import", "pygame",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--hidden-import", "yaml",
        "--hidden-import", "pymunk",
        
        # Collect all modules for problematic packages
        "--collect-all", "glcontext",
        "--collect-all", "moderngl",
        
        # Add data files (assets folder)
        "--add-data", "assets;assets",
        "--add-data", "engine;engine",
        
        # Main script
        "main.py"
    ]
    
    # Remove None values from command
    cmd = [arg for arg in cmd if arg is not None]
    
    print("Building executable with command:")
    print(" ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print("Executable created in 'dist' folder")
        if result.stdout:
            print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Build failed!")
        print("Error:", e.stderr)
        return False
    
    return True

if __name__ == "__main__":
    if build_exe():
        print("\nBuild completed successfully!")
        print("You can find your executable in the 'dist' folder")
    else:
        print("\nBuild failed. Check the error messages above.")
