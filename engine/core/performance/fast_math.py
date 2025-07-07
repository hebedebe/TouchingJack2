"""
Optimized math operations using NumPy and Numba JIT compilation
"""
import numpy as np
from numba import jit, njit
import math
from typing import Tuple, List, Union

# Fast vector operations using NumPy
Vector2 = np.ndarray

@njit(cache=True)
def fast_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Fast distance calculation using Numba JIT"""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)

@njit(cache=True)
def fast_distance_squared(x1: float, y1: float, x2: float, y2: float) -> float:
    """Fast squared distance (avoids sqrt for comparison operations)"""
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

@njit(cache=True)
def fast_normalize(x: float, y: float) -> Tuple[float, float]:
    """Fast vector normalization"""
    length = math.sqrt(x * x + y * y)
    if length == 0:
        return (0.0, 0.0)
    inv_length = 1.0 / length
    return (x * inv_length, y * inv_length)

@njit(cache=True)
def fast_lerp(a: float, b: float, t: float) -> float:
    """Fast linear interpolation"""
    return a + t * (b - a)

@njit(cache=True)
def fast_clamp(value: float, min_val: float, max_val: float) -> float:
    """Fast clamping operation"""
    return max(min_val, min(max_val, value))

@njit(cache=True)
def fast_rotate_point(x: float, y: float, angle_rad: float) -> Tuple[float, float]:
    """Fast point rotation around origin"""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)

@njit(cache=True)
def fast_angle_between(x1: float, y1: float, x2: float, y2: float) -> float:
    """Fast angle calculation between two vectors"""
    return math.atan2(y2 - y1, x2 - x1)

@njit(cache=True) 
def fast_rect_collision(x1: float, y1: float, w1: float, h1: float,
                       x2: float, y2: float, w2: float, h2: float) -> bool:
    """Fast AABB collision detection"""
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

@njit(cache=True)
def fast_circle_collision(x1: float, y1: float, r1: float,
                         x2: float, y2: float, r2: float) -> bool:
    """Fast circle collision detection"""
    dx = x2 - x1
    dy = y2 - y1
    distance_squared = dx * dx + dy * dy
    radius_sum = r1 + r2
    return distance_squared <= radius_sum * radius_sum

class FastMath:
    """Collection of optimized math operations"""
    
    # Pre-computed lookup tables for trigonometry (360 degrees)
    SIN_TABLE = np.sin(np.linspace(0, 2 * np.pi, 360, endpoint=False))
    COS_TABLE = np.cos(np.linspace(0, 2 * np.pi, 360, endpoint=False))
    
    @staticmethod
    def sin_lookup(degrees: int) -> float:
        """Fast sine lookup using pre-computed table"""
        return FastMath.SIN_TABLE[degrees % 360]
    
    @staticmethod
    def cos_lookup(degrees: int) -> float:
        """Fast cosine lookup using pre-computed table"""
        return FastMath.COS_TABLE[degrees % 360]
    
    @staticmethod
    def create_vector2(x: float = 0.0, y: float = 0.0) -> Vector2:
        """Create optimized 2D vector"""
        return np.array([x, y], dtype=np.float32)
    
    @staticmethod
    def vector2_length(vec: Vector2) -> float:
        """Fast vector length calculation"""
        return np.linalg.norm(vec)
    
    @staticmethod
    def vector2_length_squared(vec: Vector2) -> float:
        """Fast squared vector length"""
        return np.dot(vec, vec)
    
    @staticmethod
    def vector2_normalize(vec: Vector2) -> Vector2:
        """Fast vector normalization"""
        norm = np.linalg.norm(vec)
        return vec / norm if norm != 0 else vec
    
    @staticmethod
    def vector2_dot(a: Vector2, b: Vector2) -> float:
        """Fast dot product"""
        return np.dot(a, b)
    
    @staticmethod
    def vector2_distance(a: Vector2, b: Vector2) -> float:
        """Fast distance between vectors"""
        return np.linalg.norm(b - a)
    
    @staticmethod 
    def vector2_lerp(a: Vector2, b: Vector2, t: float) -> Vector2:
        """Fast linear interpolation between vectors"""
        return a + t * (b - a)
    
    @staticmethod
    def batch_transform_points(points: np.ndarray, scale: Tuple[float, float], 
                              rotation_deg: float, translation: Tuple[float, float]) -> np.ndarray:
        """Batch transform multiple points efficiently"""
        # Convert to homogeneous coordinates
        ones = np.ones((points.shape[0], 1))
        homogeneous_points = np.hstack([points, ones])
        
        # Create transformation matrix
        cos_r = FastMath.cos_lookup(int(rotation_deg))
        sin_r = FastMath.sin_lookup(int(rotation_deg))
        
        transform_matrix = np.array([
            [scale[0] * cos_r, -scale[0] * sin_r, translation[0]],
            [scale[1] * sin_r, scale[1] * cos_r, translation[1]],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # Apply transformation
        transformed = np.dot(homogeneous_points, transform_matrix.T)
        return transformed[:, :2]  # Remove homogeneous coordinate

# Compiled versions for maximum performance
distance = fast_distance
distance_squared = fast_distance_squared
normalize = fast_normalize
lerp = fast_lerp
clamp = fast_clamp
rotate_point = fast_rotate_point
angle_between = fast_angle_between
rect_collision = fast_rect_collision
circle_collision = fast_circle_collision
