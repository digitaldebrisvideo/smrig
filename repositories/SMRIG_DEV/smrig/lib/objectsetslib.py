"""
For more information about the objectSet used by the pipeline see:
http://comms-wiki/Reference/Maya/Publishing
"""
import logging

import maya.cmds as cmds
from smrig.lib import attributeslib
from smrig.lib import nodepathlib
from smrig.lib import utilslib
from smrig.lib.constantlib import RIG_SET

log = logging.getLogger("smrig.lib.objectsetslib")


def create_object_set(name, parent=RIG_SET):
	"""
	Create an object set and have the possibility to parent this set to
	a preferred object set. Ideal for handling nesting. By default any
	created set will be the child of the RIG_SET variable.

	:param str name:
	:param str/None parent:
	"""
	if not cmds.objExists(name):
		cmds.sets(name=name, empty=True)

	parent_object_set(name, parent)


def parent_object_set(name, parent):
	"""
	Parent an object set to another object set. Sanity checks are in place to
	ensure that both name and parent exist and are both of the type objectSet.

	:param str name:
	:param str parent:
	:raise ValueError: When the child set doesn't exist
	:raise ValueError: When the child set is not an objectSet
	:raise ValueError: When the parent set doesn't exist
	:raise ValueError: When the parent set is not an objectSet
	"""
	# validate name
	if not cmds.objExists(name):
		error_message = "Child '{}' doesn't exist".format(name)
		log.error(error_message)
		raise ValueError(error_message)
	elif cmds.nodeType(name) != "objectSet":
		error_message = "Child '{}' is not an objectSet".format(parent)
		log.error(error_message)
		raise ValueError(error_message)

	# validate parent
	if not cmds.objExists(parent):
		error_message = "Parent '{}' doesn't exist".format(parent)
		log.error(error_message)
		raise ValueError(error_message)
	elif cmds.nodeType(parent) != "objectSet":
		error_message = "Parent '{}' is not an objectSet".format(parent)
		log.error(error_message)
		raise ValueError(error_message)

	# catch long names
	name = nodepathlib.get_name(name)
	parent = nodepathlib.get_name(parent)

	# do parent
	if parent and name != parent:
		cmds.sets(name, add=parent)


def add_to_object_set(name, objects, parent=RIG_SET):
	"""
	The add to set function can be used to create and add objects to a object
	set at the same time. It also ensure that object set is a child of the
	RIG_SET. If the rig set doesn't exist yet it will be created. Only
	transform nodes are allowed to be part of the object sets. Any provided
	objects will be filtered to meet that criteria.

	:param str name:
	:param str/list objects:
	:param str parent:
	"""
	# make sure objects is a list
	objects = utilslib.conversion.as_list(objects)

	# create rig set if it doesn't exist
	if not cmds.objExists(RIG_SET):
		create_object_set(RIG_SET)

	# create set
	create_object_set(name, parent)

	# add objects
	for obj in objects:
		# TODO: should we just add all provided?
		if cmds.objectType(obj) in ["transform", "joint", "objectSet"]:
			cmds.sets(obj, add=name)


def add_tag_to_object_set(name, key, value=None):
	"""
	Add a tag with a value of present to the object set. If no value is
	specified the default attribute type that is created is a string
	attribute.

	:param str name:
	:param str key:
	:param str/int value:
	:raise ValueError: When the value type is not supported
	"""
	attributeslib.tag.add_tag_attribute(name, key, value)
	cmds.setAttr("{}.{}".format(name, key), edit=True, channelBox=True)


def remove_from_object_set(name, objects):
	"""
	Remove objects from the provided object set. If the objects are not part
	of the set nothing will happen. If they are they will be removed. Sanity
	checks are in place to ensure the set exists and is an actual objectSet.

	:param str name:
	:param str/list objects:
	:raise ValueError: When the set doesn't exist
	:raise ValueError: When the set is not an objectSet
	"""
	# validate set name
	if not cmds.objExists(name):
		error_message = "Set '{}' doesn't exist".format(name)
		log.error(error_message)
		raise ValueError(error_message)

	# validate set object type
	if cmds.nodeType(name) != "objectSet":
		error_message = "Object '{}' is not an objectSet".format(name)
		log.error(error_message)
		raise ValueError(error_message)

	# make sure objects is a list
	objects = utilslib.conversion.as_list(objects)

	# remove objects
	for obj in objects:
		if not cmds.objExists(obj):
			print("Object '{}' doesn't exist".format(obj))
			continue

		cmds.sets(obj, remove=name)


def remove_tag_from_object_set(name, key):
	"""
	Remove tag from the object set. If the tag doesn't exist nothing will
	happen as the desired result of not having the tag on the set is achieved.

	:param str name:
	:param str key:
	"""
	path = "{}.{}".format(name, key)
	if cmds.objExists(path):
		cmds.deleteAttr(path)
