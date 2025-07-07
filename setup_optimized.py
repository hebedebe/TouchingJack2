"""
Setup script for building optimized Cython extensions
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os

# Define Cython extensions
extensions = [
    Extension(
        "engine.core.performance.fast_math_c",
        ["engine/core/performance/fast_math_c.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math', '-march=native'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    ),
    Extension(
        "engine.core.performance.sprite_transform_c",
        ["engine/core/performance/sprite_transform_c.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math', '-march=native'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    ),
    Extension(
        "engine.core.performance.collision_c",
        ["engine/core/performance/collision_c.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math', '-march=native'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    )
]

if __name__ == "__main__":
    setup(
        name="TouchingJack2_Optimized",
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                'language_level': 3,
                'boundscheck': False,
                'wraparound': False,
                'cdivision': True,
                'nonecheck': False,
                'profile': False,
                'linetrace': False,
                'optimize.unpack_method_calls': True,
                'optimize.use_switch': True
            },
            annotate=True  # Generate HTML annotation files
        ),
        zip_safe=False,
    )
