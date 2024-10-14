import math


def frange(start, end, increment=1.0):
	"""
	:param int/float start:
	:param int/float end:
	:param float increment:
	:return: Float range
	:rtype: list
	"""
	count = int(math.ceil((end - start) / increment))
	float_range = [None] * count

	float_range[0] = start
	for i in range(1, count):
		float_range[i] = float_range[i - 1] + increment

	return float_range
