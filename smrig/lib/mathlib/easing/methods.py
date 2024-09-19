import math

__all__ = [
	"linear",
	"quadratic_in_out",
	"quadratic_in",
	"quadratic_out",
	"cubic_in_out",
	"cubic_in",
	"cubic_out",
	"quartic_in_out",
	"quartic_in",
	"quartic_out",
	"quintic_in_out",
	"quintic_in",
	"quintic_out",
	"sine_in_out",
	"sine_in",
	"sine_out",
	"exponential_in_out",
	"exponential_in",
	"exponential_out"
]


# LINEAR
def linear(t):
	"""
	:param float/int t:
	:return: Linear ease in out
	:rtype: float
	"""
	return t


# QUADRATIC
def quadratic_in_out(t):
	"""
	:param float/int t:
	:return: Quadratic ease in out
	:rtype: float
	"""
	if t < 0.5:
		return 2.0 * t ** 2

	return (-2.0 * t * t) + (4.0 * t) - 1.0


def quadratic_in(t):
	"""
	:param float/int t:
	:return: Quadratic ease in
	:rtype: float
	"""
	return t ** 2


def quadratic_out(t):
	"""
	:param float/int t:
	:return: Quadratic ease out
	:rtype: float
	"""
	return -(t * (t - 2.0))


# CUBIC
def cubic_in_out(t):
	"""
	:param float/int t:
	:return: Cubic ease in out
	:rtype: float
	"""
	if t < 0.5:
		return 4.0 * t ** 3

	p = 2 * t - 2
	return 0.5 * p ** 3 + 1.0


def cubic_in(t):
	"""
	:param float/int t:
	:return: Cubic ease in
	:rtype: float
	"""
	return t ** 3


def cubic_out(t):
	"""
	:param float/int t:
	:return: Cubic ease out
	:rtype: float
	"""
	return (t - 1) ** 3 + 1.0


# QUARTIC
def quartic_in_out(t):
	"""
	:param float/int t:
	:return: Quartic ease in out
	:rtype: float
	"""
	if t < 0.5:
		return 8.0 * t ** 4

	p = t - 1
	return -8.0 * p ** 4 + 1.0


def quartic_in(t):
	"""
	:param float/int t:
	:return: Quartic ease in
	:rtype: float
	"""
	return t ** 4


def quartic_out(t):
	"""
	:param float/int t:
	:return: Quartic ease out
	:rtype: float
	"""
	return (t - 1) ** 4 + 1.0


# QUINTIC
def quintic_in_out(t):
	"""
	:param float/int t:
	:return: Quintic ease in out
	:rtype: float
	"""
	if t < 0.5:
		return 16.0 * t ** 5

	p = (2 * t) - 2
	return 0.5 * p ** 5 + 1


def quintic_in(t):
	"""
	:param float/int t:
	:return: Quintic ease in
	:rtype: float
	"""
	return t ** 5


def quintic_out(t):
	"""
	:param float/int t:
	:return: Quintic ease out
	:rtype: float
	"""
	return (t - 1) ** 5 + 1.0


# SINE
def sine_in_out(t):
	"""
	:param float/int t:
	:return: Sine ease in out
	:rtype: float
	"""
	return 0.5 * (1.0 - math.cos(t * math.pi))


def sine_in(t):
	"""
	:param float/int t:
	:return: Sine ease in
	:rtype: float
	"""
	return math.sin((t - 1.0) * math.pi / 2.0) + 1.0


def sine_out(t):
	"""
	:param float/int t:
	:return: Sine ease out
	:rtype: float
	"""
	return math.sin(t * math.pi / 2.0)


# CIRCULAR
def circular_in_out(t):
	"""
	:param float/int t:
	:return: Circular ease in out
	:rtype: float
	"""
	if t < 0.5:
		return 0.5 * (1.0 - math.sqrt(1.0 - 4.0 * (t * t)))

	return 0.5 * (math.sqrt(-((2.0 * t) - 3.0) * ((2.0 * t) - 1.0)) + 1.0)


def circular_in(t):
	"""
	:param float/int t:
	:return: Circular ease in
	:rtype: float
	"""
	return 1.0 - math.sqrt(1.0 - (t * t))


def circular_out(t):
	"""
	:param float/int t:
	:return: Circular ease out
	:rtype: float
	"""
	return math.sqrt((2.0 - t) * t)


# EXPONENTIAL
def exponential_in_out(t):
	"""
	:param float/int t:
	:return: Exponential ease in out
	:rtype: float
	"""
	if t == 0.0 or t == 1.0:
		return t

	if t < 0.5:
		return 0.5 * math.pow(2, (20 * t) - 10)

	return -0.5 * math.pow(2, (-20 * t) + 10) + 1.0


def exponential_in(t):
	"""
	:param float/int t:
	:return: Exponential ease in
	:rtype: float
	"""
	if t == 0.0:
		return 0.0

	return math.pow(2, 10 * (t - 1))


def exponential_out(t):
	"""
	:param float/int t:
	:return: Exponential ease out
	:rtype: float
	"""
	if t == 1.0:
		return 1.0

	return 1.0 - math.pow(2, -10 * t)
