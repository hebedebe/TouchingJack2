@echo off
echo Building optimized Touching Jack 2...

REM Install required packages
echo Installing optimization dependencies...
pip install cython numpy numba psutil

REM Build Cython extensions
echo Building Cython extensions for maximum performance...
python setup_optimized.py build_ext --inplace

REM Check if build was successful
if errorlevel 1 (
    echo Warning: Cython extensions failed to build. Game will run with Python optimizations only.
    pause
) else (
    echo Cython extensions built successfully!
)

echo.
echo Optimization complete! Run the game with:
echo python main.py
echo.
echo Performance features enabled:
echo - Advanced sprite caching system
echo - Object pooling for memory efficiency  
echo - OpenGL batch rendering
echo - Optimized math operations with Numba/Cython
echo - Intelligent memory management
echo - Asset preloading and caching
echo.
pause
