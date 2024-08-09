from functools import cache
import re
from typing import Optional

import numpy as np


def camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def deg_to_compass(degrees: float) -> Optional[str]:
    """
    Converts a wind direction in degrees to the corresponding compass direction.

    Args:
      degrees (float): Wind direction in degrees (0 to 360).

    Returns:
      str: The compass direction (e.g., "N", "NE", "SW").
    """

    if degrees is None or np.isnan(degrees):
        return None

    val = int((degrees / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]


@cache
def wind_speed_to_beaufort(wind_speed) -> Optional[int]:
    """
    This function converts wind speed in kilometers per hour (kmph) to the Beaufort scale force.

    Args:
    wind_speed: Wind speed in kilometers per hour (kmph).

    Returns:
    The Beaufort scale force (integer) or None if wind speed is negative.
    """
    if wind_speed is None or np.isnan(wind_speed) or wind_speed < 0:
        return None

    beaufort_scale = {
        0: (0, 1),
        1: (1, 6),
        2: (6, 12),
        3: (12, 20),
        4: (20, 29),
        5: (29, 38),
        6: (38, 50),
        7: (50, 62),
        8: (62, 75),
        9: (75, 89),
        10: (89, 103),
        11: (103, 118),
        12: (118, float('inf')),
    }

    return next(force for force, (lb, ub) in beaufort_scale.items() if lb <= wind_speed < ub)
