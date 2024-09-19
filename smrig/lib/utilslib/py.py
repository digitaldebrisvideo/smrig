import inspect
import logging
import os
import pkgutil
import sys
import traceback

try:
	from collections.abc import Mapping
except ImportError:
	from collections import Mapping

from collections import abc

MutableMapping = abc.MutableMapping

# try:
#     from collections.abc import MutableMapping
# except ImportError:
#     from collections import Mapping

try:
	from importlib import reload
except:
	pass

log = logging.getLogger("smrig.lib.utilslib.py")


class Singleton(type):
	"""
	This type can be set as the __metaclass__ in a class and will turn it into
	a singleton.
	"""
	_instances = {}

	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class AttributeDict(MutableMapping):
	"""
	The AttributeDict class is a class that links dictionary still assignments
	with its attributes. This means that the class can be used as a dictionary
	or/and access its keys directly. A list of protected attributes is
	retrieved in the init and any attributes defined before the init is called
	will be excluded from the dict style accessing.
	"""
	_protected_attributes = set()
	_error_message = "Item '{}' is a protected attribute and cannot be {} " \
	                 "using dict style."

	def __init__(self, dict_):
		self._protected_attributes = dir(self)
		self.__dict__ = dict_

	def __delitem__(self, v):
		if v in self._protected_attributes:
			error_message = self._error_message.format(v, "removed")
			log.error(error_message)
			raise KeyError(error_message)

		self.__delattr__(v)

	def __getitem__(self, k):
		if k in self._protected_attributes:
			error_message = self._error_message.format(k, "retrieved")
			log.error(error_message)
			raise KeyError(error_message)

		try:
			return self.__getattribute__(k)
		except AttributeError as e:
			raise KeyError(str(e))

	def __iter__(self):
		for attr in dir(self):
			# ignore private and ignore attributes
			if not self.is_protected_attribute(attr):
				yield attr

	def __len__(self):
		return len(list(self.__iter__()))

	def __setitem__(self, k, v):
		if k in self._protected_attributes:
			error_message = self._error_message.format(k, "set")
			log.error(error_message)
			raise KeyError(error_message)

		self.__setattr__(k, v)

	# ------------------------------------------------------------------------

	def is_protected_attribute(self, k):
		"""
		:param str k:
		:return: Protected attribute state
		:rtype: bool
		"""
		state = True if k.startswith("_") or k in self._protected_attributes else False
		return state


def reload_hierarchy(obj):
	"""
	Reload the module and all of its children. Ideal for refreshing all or
	certain parts of the pipeline.

	Example:
		.. code-block:: python

			# reload lib
			from smrig import lib
			reload_hierarchy(lib)

	:param obj:
	"""
	# variables
	modules = []
	path = obj.__path__
	prefix = obj.__name__ + "."

	# get modules
	for _, module_name, _ in pkgutil.walk_packages(path, prefix):
		if module_name not in sys.modules:
			continue

		modules.append(module_name)

	# reload modules in reverse
	for module_name in reversed(modules):
		module_ = sys.modules.pop(module_name)
		sys.modules[module_name] = module_
		reload(module_)
		log.debug("Reload: '{}'".format(module_name))

	# reload parent
	reload(obj)
	log.debug("Reload: '{}'".format(obj.__name__))


def get_full_name(obj):
	"""
	Get the objects full name by appending the objects name to the objects
	module path.

	:param obj:
	:return: Objects full path
	:rtype: str
	"""
	return ".".join([obj.__module__, obj.__name__])


def get_function_file_path(func):
	"""
	Find file name from imported function or module.

	:param func: module / function
	:return:
	"""
	mod = inspect.getmodule(func)
	file_path = inspect.getfile(mod).replace(".pyc", ".py")

	return file_path if os.path.isfile(file_path) else None


def is_subclass(class_, class_info):
	"""
	This function determines if class_ is a subclass of class_info or of the
	same type is class_info. The normal issubclass function will fail when
	modules are reloaded. This method checks based on the full path of the
	object rather than its hash.

	:param class_:
	:param class_info:
	:return: Subclass state
	:rtype: type
	"""
	if inspect.isclass(class_):
		search_name = get_full_name(class_info)
		inherited_names = [get_full_name(c) for c in inspect.getmro(class_)]
		if search_name in inherited_names:
			return True

	return False


def get_exception():
	"""
	Get exception traceback formatted as a string.

	:return: traceback
	:rtype: str
	"""
	return "".join(traceback.format_exception(*sys.exc_info()))


def get_exception_info(exception):
	"""
	Break out an exception into the exception name and message as strings.

	:param Exception exception:
	:return: exception type, exception message
	:rtype: tuple(str, str)
	"""
	try:
		result = [type(exception.args[0]).__name__, exception.args[0][0]]
		result = result if result else ["Error", exception]
		return result

	except:
		pass
