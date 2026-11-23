from vpython import vector

def to_vpython(p):
    """Dataset uses Z-up; VPython uses Y-up."""
    return vector(float(p[0]), float(p[2]), -float(p[1]))
