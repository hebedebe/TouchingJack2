# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

"""
Cython-optimized math functions for maximum performance
"""

import cython
import numpy as np
cimport numpy as cnp
from libc.math cimport sqrt, cos, sin, atan2, fabs

ctypedef cnp.float32_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline DTYPE_t c_distance(DTYPE_t x1, DTYPE_t y1, DTYPE_t x2, DTYPE_t y2) nogil:
    """Ultra-fast distance calculation"""
    cdef DTYPE_t dx = x2 - x1
    cdef DTYPE_t dy = y2 - y1
    return sqrt(dx * dx + dy * dy)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline DTYPE_t c_distance_squared(DTYPE_t x1, DTYPE_t y1, DTYPE_t x2, DTYPE_t y2) nogil:
    """Ultra-fast squared distance (avoids sqrt)"""
    cdef DTYPE_t dx = x2 - x1
    cdef DTYPE_t dy = y2 - y1
    return dx * dx + dy * dy

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline void c_normalize(DTYPE_t x, DTYPE_t y, DTYPE_t* out_x, DTYPE_t* out_y) nogil:
    """Ultra-fast vector normalization"""
    cdef DTYPE_t length = sqrt(x * x + y * y)
    if length == 0:
        out_x[0] = 0
        out_y[0] = 0
    else:
        cdef DTYPE_t inv_length = 1.0 / length
        out_x[0] = x * inv_length
        out_y[0] = y * inv_length

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline DTYPE_t c_lerp(DTYPE_t a, DTYPE_t b, DTYPE_t t) nogil:
    """Ultra-fast linear interpolation"""
    return a + t * (b - a)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline DTYPE_t c_clamp(DTYPE_t value, DTYPE_t min_val, DTYPE_t max_val) nogil:
    """Ultra-fast clamping"""
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    else:
        return value

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline bint c_rect_collision(DTYPE_t x1, DTYPE_t y1, DTYPE_t w1, DTYPE_t h1,
                                  DTYPE_t x2, DTYPE_t y2, DTYPE_t w2, DTYPE_t h2) nogil:
    """Ultra-fast AABB collision detection"""
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline bint c_circle_collision(DTYPE_t x1, DTYPE_t y1, DTYPE_t r1,
                                    DTYPE_t x2, DTYPE_t y2, DTYPE_t r2) nogil:
    """Ultra-fast circle collision detection"""
    cdef DTYPE_t dx = x2 - x1
    cdef DTYPE_t dy = y2 - y1
    cdef DTYPE_t distance_squared = dx * dx + dy * dy
    cdef DTYPE_t radius_sum = r1 + r2
    return distance_squared <= radius_sum * radius_sum

# Python-accessible functions
def fast_distance(float x1, float y1, float x2, float y2):
    """Fast distance calculation - Python interface"""
    return c_distance(x1, y1, x2, y2)

def fast_distance_squared(float x1, float y1, float x2, float y2):
    """Fast squared distance - Python interface"""
    return c_distance_squared(x1, y1, x2, y2)

def fast_normalize(float x, float y):
    """Fast normalization - Python interface"""
    cdef DTYPE_t out_x, out_y
    c_normalize(x, y, &out_x, &out_y)
    return (out_x, out_y)

def fast_lerp(float a, float b, float t):
    """Fast lerp - Python interface"""
    return c_lerp(a, b, t)

def fast_clamp(float value, float min_val, float max_val):
    """Fast clamp - Python interface"""
    return c_clamp(value, min_val, max_val)

def fast_rect_collision(float x1, float y1, float w1, float h1,
                       float x2, float y2, float w2, float h2):
    """Fast rect collision - Python interface"""
    return c_rect_collision(x1, y1, w1, h1, x2, y2, w2, h2)

def fast_circle_collision(float x1, float y1, float r1,
                         float x2, float y2, float r2):
    """Fast circle collision - Python interface"""
    return c_circle_collision(x1, y1, r1, x2, y2, r2)

@cython.boundscheck(False)
@cython.wraparound(False)
def batch_transform_points(cnp.ndarray[DTYPE_t, ndim=2] points,
                          DTYPE_t scale_x, DTYPE_t scale_y,
                          DTYPE_t rotation_rad, DTYPE_t trans_x, DTYPE_t trans_y):
    """Batch transform points for maximum performance"""
    cdef int num_points = points.shape[0]
    cdef cnp.ndarray[DTYPE_t, ndim=2] result = np.empty((num_points, 2), dtype=np.float32)
    
    cdef DTYPE_t cos_r = cos(rotation_rad)
    cdef DTYPE_t sin_r = sin(rotation_rad)
    
    cdef int i
    cdef DTYPE_t x, y, scaled_x, scaled_y
    
    for i in range(num_points):
        x = points[i, 0]
        y = points[i, 1]
        
        # Apply scaling
        scaled_x = x * scale_x
        scaled_y = y * scale_y
        
        # Apply rotation
        result[i, 0] = scaled_x * cos_r - scaled_y * sin_r + trans_x
        result[i, 1] = scaled_x * sin_r + scaled_y * cos_r + trans_y
    
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
def batch_distance_check(cnp.ndarray[DTYPE_t, ndim=2] points1,
                        cnp.ndarray[DTYPE_t, ndim=2] points2,
                        DTYPE_t max_distance):
    """Batch distance checking for spatial queries"""
    cdef int num_points1 = points1.shape[0]
    cdef int num_points2 = points2.shape[0]
    cdef list results = []
    
    cdef DTYPE_t max_dist_squared = max_distance * max_distance
    cdef int i, j
    cdef DTYPE_t dist_squared
    
    for i in range(num_points1):
        for j in range(num_points2):
            dist_squared = c_distance_squared(points1[i, 0], points1[i, 1],
                                            points2[j, 0], points2[j, 1])
            if dist_squared <= max_dist_squared:
                results.append((i, j, sqrt(dist_squared)))
    
    return results
