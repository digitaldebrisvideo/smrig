import logging

import maya.mel as mel

log = logging.getLogger("smrig.lib.utilslib.mel")


def get_mel_global_variable(variable):
	"""
	:param str variable:
	:return: Mel global variable
	:rtype: str
	:raise ValueError: If the variable doesn't exist
	"""
	# get variable type
	variable_array = ""
	variable_type = mel.eval("whatIs \"{}\"".format(variable))
	variable_type = variable_type.split()[0]

	# validate variable
	if variable_type == "Unknown":
		error_message = "MEL variable '{}' doesn't exist.".format(variable)
		log.error(error_message, exc_info=1)
		raise ValueError(error_message)

	# populate variable type and array
	if variable_type.endswith("[]"):
		variable_type = variable_type[:-2]
		variable_array = "[]"

	# get variable
	return mel.eval("{1} {0}_temp{2} = {0};".format(variable, variable_type, variable_array))


def get_all_mel_global_variables():
	"""
	:return: All mel global variables
	:rtype: dict
	"""
	return {
		variable: get_mel_global_variable(variable)
		for variable in mel.eval("env")
	}
