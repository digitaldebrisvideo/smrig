import re


def split_camel_and_snake_case(name):
	"""
	Wrapper for split_snake_case and split_camel_case.

	:param str name:
	:return: Split names
	:rtype: list
	"""
	return [v for sublist in [split_camel_case(t) for t in split_snake_case(name)] for v in sublist]


def split_snake_case(name):
	"""
	:param str name:
	:return: Split names
	:rtype: list
	"""
	return name.split("_")


def split_camel_case(name):
	"""
	:param str name:
	:return: Split names
	:rtype: list
	"""
	matches = re.finditer(".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", name)
	return [m.group(0) for m in matches]


def split_by_int(name):
	"""
	Split a string by integers.

	:param str name:
	:return:
	:rtype: list
	"""
	result = [v for sublist in [list(t) for t in re.findall(r'(\w+?)(\d+)', name)] for v in sublist]
	return result if result else [name]


# ----------------------------------------------------------------------------

def capitalize(name):
	"""
	Capitalize while keeping camelCase.

	:param name:
	:return: str
	"""
	return "{}{}".format(name[0].upper(), name[1:]) if len(name) > 1 else name


def upper_camel_to_snake_case(name):
	"""
	:param str name:
	:return: Snake case name
	:rtype: str
	"""
	names = split_camel_case(name)
	return "_".join([name.lower() for name in names])


def snake_to_upper_camel_case(name):
	"""
	:param name:
	:return: Upper camel case name
	:rtype: str
	"""
	return "".join([n[0].upper() + n[1:] for n in name.split("_") if n])


def snake_to_lower_camel_case(name):
	"""
	:param name:
	:return: Lower camel case name
	:rtype: str
	"""
	upper_camel_case = snake_to_upper_camel_case(name)
	return upper_camel_case[0].lower() + upper_camel_case[1:]


def snake_case_to_nice_name(name):
	"""
	Convert snake case to a nice case format. This is done by replacing the
	underscores with spaces and upper casing each section.

	:param str name:
	:return: Nice name
	:rtype: str
	"""
	return " ".join([n.capitalize() for n in name.split("_")])


def camel_case_to_nice_name(name):
	"""
	Convert camel case to a nice case format. This is done by replacing the
	capital letters with spaces and upper casing each section.

	:param str name:
	:return: Nice name
	:rtype: str
	"""
	return " ".join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', name[0].upper() + name[1:]))


# ----------------------------------------------------------------------------


def mirror_name(name, left_side='L', right_side='R'):
	"""

	Return the mirrored name

	If no mirrorpart is found, return None

	:param str name: name to mirrorpart
	:param str left_side: Prefix that defines left side names
	:param str right_side: Prefix that defines right names
	:return: Mirrored name
	:rtype: str/None
	"""

	mirrored_name = None

	if name.startswith(left_side):
		mirrored_name = name.replace(left_side, right_side, 1)

	elif name.startswith(right_side):
		mirrored_name = name.replace(right_side, left_side, 1)

	return mirrored_name
