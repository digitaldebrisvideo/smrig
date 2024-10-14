import functools
import logging
import time

import maya.cmds as cmds

from smrig.lib import utilslib

log = logging.getLogger("smrig.lib.decoratorslib")


def singleton(class_):
	"""
	a singleton. Use as a decorator for python 2 and 3 compatability
	"""
	instances = {}

	def get_instance(*args, **kwargs):
		if class_ not in instances:
			instances[class_] = class_(*args, **kwargs)
		return instances[class_]

	return get_instance


def timer(func):
	"""
	The timer decorator will print the fill name of the function and the
	duration of the execution of that function. This is ideal to keep track
	of more time consuming methods and benchmark their speed.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		# get module
		full_name = []

		# get class, classes are parsed as self into functions, this means that it
		# is possible the first argument parsed into the function can be used to
		# extract the class name
		if args and "__class__" in dir(args[0]):
			full_name.append(args[0].__class__.__name__)

		# append name
		full_name.append(func.__name__)
		full_name = ".".join(full_name)

		# store time
		t = time.time()

		# call function
		ret = func(*args, **kwargs)

		# print time it took function to run
		log.info("{0} was executed in {1:.3f} seconds".format(full_name, time.time() - t))
		return ret

	return wrapper


def memoize(func):
	"""
	The memoize decorator will cache the result of a function using its
	arguments and keyword arguments. This can come in handy to cache the
	result of time consuming functions.
	"""
	cache = {}

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		key = str(args) + str(kwargs)
		if key not in cache:
			cache[key] = func(*args, **kwargs)

		return cache[key]

	def cache_clear():
		cache.clear()

	wrapper.cache_clear = cache_clear
	return wrapper


def deprecated(location=None, functionality=False, arguments=False):
	"""
	The deprecated function can be assigned to functions that are no longer
	meant to be used. The decorator will prevent these functions from running
	but will print the message provided which could inform the user about an
	alternative or where the function may have moved too.

	:param str/None location:
	:param bool functionality:
	:param bool arguments:
	"""

	def decorator(func):
		def wrapper(*args, **kwargs):
			messages = []

			if not location:
				messages.append("Deprecated: function '{}' not used by system.".format(func.__name__))
			else:
				messages.append("Moved: '{}'.".format(location))

			if functionality:
				messages.append("Functionality changed: have a look at the source code.")

			if arguments:
				messages.append("Arguments changed: have a look at the source code.")

			message = "\n".join(messages)
			log.error(message)
			raise RuntimeError(message)

		return wrapper

	return decorator


def preserve_selection(func):
	"""
	The preserve selection function will store the current selection in maya
	before the function is ran and will restore it once the function has
	completed.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		selection = cmds.ls(sl=True)
		ret = func(*args, **kwargs)

		if selection:
			try:
				if selection:
					cmds.select(selection, noExpand=True)
				else:
					cmds.select(clear=True)

			except:
				cmds.select(clear=True)

		else:
			cmds.select(clear=True)

		return ret

	return wrapper


def undoable(func):
	"""
	The undoable decorator will wrap the function in an undo queue. Ideally to
	be used when UI functions call upon the system. QT is notorious for
	breaking an undo chunk into individual functions.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		with utilslib.undo.UndoChunk():
			return func(*args, **kwargs)

	return wrapper


def refresh_viewport(func):
	"""
	The preserve selection function will store the current selection in maya
	before the function is ran and will restore it once the function has
	completed.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		ret = func(*args, **kwargs)
		cmds.refresh()
		return ret

	return wrapper


def null_viewport(func):
	"""
	This will make the current viewport into a static editor
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		model_panel = utilslib.viewport.set_dull_panel()

		try:
			ret = func(*args, **kwargs)
			utilslib.viewport.set_model_panel(model_panel)
			return ret

		except Exception as e:
			utilslib.viewport.set_model_panel(model_panel)
			raise e

	return wrapper
