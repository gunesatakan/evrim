"""World-space dimensions shared by weapon bodies, projectiles and range checks."""
import math


def carrier_scale(radius, power, carrier):
    radius = max(0.0, float(radius))
    power = max(0.0, float(power))
    if int(carrier) == 3:
        # A stronger contractile sheath need not be arbitrarily longer.
        # The full 66-unit apparatus occupies at most 60% of the cell radius.
        growth = 0.65 + 0.35 * (1.0 - math.exp(-power))
        return radius / 110.0 * growth
    return radius / 110.0 * power
