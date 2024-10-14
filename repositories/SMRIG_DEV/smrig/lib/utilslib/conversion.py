import logging

log = logging.getLogger("smrig.lib.utilslib.conversion")

import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)
else:
    string_types = (str,)


def as_int(string_):
	"""
	Convert a string to an int, if possible.

	:param string_:
	:return:
	"""
	try:
		return int(string_)

	except:
		log.debug("Could not convert {}".format(string_))


def as_str(data, unicode_only=True):
	"""
	Convert unicode to string

	:param data:
	:param unicode_only: Ignore if the data is not unidode:

	:return:
	"""
	if unicode_only and isinstance(data, string_types):
		return str(data)

	elif not unicode_only:
		return str(data)

	return data


def as_list(data):
	"""
	Convert any dataexporter into a list.

	:param str/list/tuple/None data:
	:return: Selection
	:rtype: list
	:raise ValueError: When the provided type is not supported
	"""
	if data is None:
		return []
	elif isinstance(data, string_types):
		return [data]
	elif isinstance(data, list):
		return data
	elif isinstance(data, tuple):
		return list(data)
	elif isinstance(data, int):
		return [data]
	elif isinstance(data, float):
		return [data]

	error_message = "Unable to convert type '{}' to list.".format(type(data))
	log.error(error_message, exc_info=1)
	raise ValueError(error_message)


def as_chunks(list_, num):
	"""
	:param list list_:
	:param int num:
	:return: Provided list split in chunks of size num
	:rtype: list
	"""
	return [
		list_[i:i + num]
		for i in range(0, len(list_), num)
	]


def split_list(list_, num):
	"""
	Split a list into N number of lists of roughly equal sizes.

	:param list list_:
	:param int num: number of splits
	:return: List of lists
	:rtype: list
	"""
	k, m = divmod(len(list_), num)
	return list(list_[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num))


def get_first(list_):
	"""
	:param list list_:
	:return: First object in list
	:rtype: str/None
	"""
	if list_:
		return list_[0]


def get_middle(list_):
	"""
	The the middle entry of a list. If the lists length is of an even number
	the two most middle items are returned. Because if this the middle is
	always returned as a list. The number of items returned as provided for
	easy error checking.

	:param list list_:
	:return: Middle item, num items returned
	:rtype: tuple
	"""
	if not list_:
		return []

	length = len(list_)
	index = int(length * 0.5 - 0.5)
	indices = [index]

	if not length % 2:
		indices.append(index + 1)

	return [list_[i] for i in indices], len(indices)


def get_difference(full_data, data):
	"""
	Subtract the items in the dataexporter variable from the full dataexporter variable. Ideal
	to get differences in axis and channels for example.

	:param list full_data:
	:param str/list data:
	:return: Difference
	:rtype: list
	"""
	data = as_list(data)
	return list(set(full_data) - set(data))
