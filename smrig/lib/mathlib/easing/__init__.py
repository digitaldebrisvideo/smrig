import logging
from collections import OrderedDict

from smrig.lib.mathlib.easing import methods
from smrig.lib.mathlib.easing.methods import *

log = logging.getLogger("smrig.lib.mathlib.easing")

EASING_MAPPER = OrderedDict([(name, getattr(methods, name)) for name in methods.__all__])


def ease(method_name, value):
	"""
	:param method_name:
	:param value:
	:return: Eased value
	"""
	return get_easing_method(method_name)(value)


def get_easing_method(method_name):
	"""
	:param str method_name:
	:return: Easing function
	:rtype: func
	:raise ValueError: When the easing function doesn't exist.
	"""
	func = EASING_MAPPER.get(method_name)

	if not func:
		easing_methods = get_all_easing_methods()
		error_message = "No easing methods found using name '{}', options are {}".format(name, easing_methods)
		log.error(error_message)
		raise ValueError(error_message)

	return func


def get_all_easing_methods():
	"""
	:return: All available easing methods
	:rtype: list
	"""
	return EASING_MAPPER.keys()
