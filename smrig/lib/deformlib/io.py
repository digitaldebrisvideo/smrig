import logging
import os
from collections import OrderedDict

import maya.cmds as cmds

from smrig.lib import nodepathlib
from smrig.lib import utilslib
from smrig.lib.deformlib.xml import DeformerWeightsXML

log = logging.getLogger("smrig.lib.deformlib.io")


class DeformerWeightsIO(object):
	def __init__(self, node):
		self._node = node
		self._node_shape = cmds.listRelatives(node, shapes=True, noIntermediate=True)[0]
		self._node_shape_type = cmds.nodeType(self._node_shape)
		self._xml = None

		self._weight_precision = 5
		self._weight_tolerance = 0.001
		self._supported_import_types = ["weightGeometryFilter", "skinCluster", "blendShape"]
		self._supported_export_types = ["weightGeometryFilter", "skinCluster", "blendShape"]

	# ------------------------------------------------------------------------

	@property
	def name(self):
		"""
		:return: Name
		:rtype: str
		"""
		return nodepathlib.get_leaf_name(self.node)

	# ------------------------------------------------------------------------

	@property
	def node(self):
		"""
		:return: Node
		:rtype: str
		"""
		return self._node

	@property
	def node_shape(self):
		"""
		:return: Node shape
		:rtype: str
		"""
		return self._node_shape

	@property
	def node_shape_type(self):
		"""
		:return: Node shape type
		:rtype: str
		"""
		return self._node_shape_type

	# ------------------------------------------------------------------------

	@property
	def xml(self):
		"""
		:param :class:`smrig.lib.deformlib.xml.DeformerWeightsXML` xml
		:return: Deformer weights xml
		:rtype: :class:`smrig.lib.deformlib.xml.DeformerWeightsXML`
		"""
		return self._xml

	@xml.setter
	def xml(self, xml):
		self._xml = xml

	# ------------------------------------------------------------------------

	def get_deformers(self, deformer_types):
		"""
		:param str/list deformer_types:
		:return: Deformers
		:rtype: list
		"""
		deformers = []
		deformer_types = utilslib.conversion.as_list(deformer_types)

		for node in cmds.listHistory(self.node_shape) or []:
			inherited = cmds.nodeType(node, inherited=True)
			for inherit in deformer_types:
				if inherit in inherited:
					deformers.append(node)
					break

		return deformers

	# ------------------------------------------------------------------------

	def extract_xml_deformer_attribute_data(self, attributes):
		"""
		Extract attribute information in a way that it can be used together
		with the maya cmds.setAttr command. This function will split the
		saved attributes into args and kwargs that can be passed to the
		cmds.setAttr command.

		:param list attributes:
		:return: Attributes
		:rtype: list
		"""
		# variable
		attribute_data = {}
		for attribute in attributes:
			# variables
			attribute_args = []
			attribute_kwargs = {}

			# get dataexporter
			attribute_name = attribute.get("name")
			attribute_type = attribute.get("type")
			attribute_value = attribute.get("value")
			attribute_multi = attribute.get("multi")

			# populate variables
			attribute_values = attribute_value.split()

			if attribute_type == "bool":
				attribute_args.append(True if attribute_value == "1" else False)
			elif attribute_type == "string":
				attribute_args.append(attribute_value)
				attribute_kwargs["string"] = True
			elif attribute_type in ["float", "double", "double3", "doubleAngle"]:
				attribute_args.extend([float(v) for v in attribute_values])
			elif attribute_type in ["integer", "long", "enum"]:
				attribute_args.extend([int(v) for v in attribute_values])

			# store attributes
			if attribute_multi:
				attribute_multi = attribute_multi.split()

				for m, a in zip(attribute_multi, attribute_args):
					attribute_data["{}[{}]".format(attribute_name, m)] = {
						"args": [a],
						"kwargs": attribute_kwargs
					}
			else:
				attribute_data[attribute_name] = {
					"args": attribute_args,
					"kwargs": attribute_kwargs
				}

		return attribute_data

	def extract_xml_deformer_data(self, deformer_types=None):
		"""
		Extract valid deformer dataexporter from file. Both the user input deformer
		types and the internal deformer types that are allowed by the class
		will be checked, if the check doesn't pass the deformer dataexporter will not
		be returned. Only the deformer names and their attributes will be
		stored.

		:param list/None deformer_types:
		:return: Deformer dataexporter
		:rtype: dict
		"""
		# variable
		extracted_data = OrderedDict()

		# process deformers
		deformers = self.xml.get_deformers()
		for deformer_name, deformer in deformers.items():
			# validate external deformer types
			deformer_type = deformer.get("type")
			if deformer_types and deformer_type not in deformer_types:
				continue

			# validate internal deformer types
			internal_state = False
			inherited = cmds.nodeType(deformer_type, inherited=True, isTypeName=True)
			for inherit in self._supported_import_types:
				if inherit in inherited:
					internal_state = True
					break

			if not internal_state:
				continue

			# get name
			deformer_name = deformer.get("name")

			# get attributes
			attributes = self.xml.get_deformer_attributes(deformer_name)
			extracted_data[deformer_name] = {
				"type": deformer_type,
				"attributes": self.extract_xml_deformer_attribute_data(attributes)
			}

		return extracted_data

	# ------------------------------------------------------------------------

	def set_deformer_attributes(self, deformer, attributes):
		"""
		Loop the attributes dictionary and set all the attributes on the
		deformer node if they can be set.

		:param str deformer:
		:param dict attributes:
		"""
		# loop attributes
		for attribute_name, attribute_data in attributes.items():
			# get attribute full path
			attr_path = "{}.{}".format(deformer, attribute_name)

			# validate attribute
			if cmds.getAttr(attr_path, lock=True):
				log.warning("Could not set attribute '{}', it is locked!".format(attr_path))
				continue
			elif cmds.listConnections(attr_path, source=True, destination=False):
				log.warning("Could not set attribute '{}', it has incoming connections!".format(attr_path))
				continue

			# unpack args and kwargs
			args = attribute_data.get("args")
			args.insert(0, attr_path)
			kwargs = attribute_data.get("kwargs")

			# set attribute
			cmds.setAttr(*args, **kwargs)

	# ------------------------------------------------------------------------

	def export_weights(self, file_path, deformer_types=None, remove_namespaces=True):
		"""
		Export all deformers into an xml file using the cmds.deformerWeights
		function. All of the attributes on these deformers will also
		be stored in the exported file. The deformer_types variable can be
		used to only export certain deformer types.

		:param str file_path:
		:param str/list deformer_types:
		:param bool remove_namespaces:
		:return: File path
		:rtype: str
		:raise RuntimeError: When no deformers are found
		"""
		# create directory if it doesn't exist
		directory = os.path.dirname(file_path)
		if not os.path.exists(directory):
			os.makedirs(directory)

		# filter deformers
		deformer_types = utilslib.conversion.as_list(deformer_types)

		deformers = [
			deformer
			for deformer in self.get_deformers(self._supported_export_types)
			if not deformer_types or cmds.nodeType(deformer) in deformer_types
		]

		# validate deformers
		if not deformers:
			error_message = "No deformers found on '{}'!".format(self.node)
			log.error(error_message, exc_info=1)
			raise RuntimeError(error_message)

		# get deformers attributes
		# TODO: find a nice way to only extract the attributes needed.
		deformer_attributes = cmds.listAttr(deformers)

		# get directory and file name
		directory, file_name = os.path.split(file_path)

		# export weights
		cmds.deformerWeights(
			file_name,
			path=directory,
			export=True,
			shape=self.node_shape,
			deformer=deformers,
			attribute=deformer_attributes,
			weightPrecision=self._weight_precision,
			weightTolerance=self._weight_tolerance
		)

		# remove namespaces
		if remove_namespaces and os.path.exists(file_path):
			self.xml = DeformerWeightsXML.load(file_path)
			self.xml.remove_namespaces()
			self.xml.save()

		return file_path

	@classmethod
	def export_weights_multi(cls, nodes, directory, deformer_types=None, remove_namespaces=True):
		"""
		Export all deformers into an xml file using the cmds.deformerWeights
		function. All of the attributes on these deformers will also
		be stored in the exported file. The deformer_types variable can be
		used to only export certain deformer types. All nodes will be looped
		and have their deformer weights exported.

		:param list nodes:
		:param str directory:
		:param bool remove_namespaces:
		:param str/list/None deformer_types:
		"""
		for node in nodes:
			# get file name
			file_name = "{}.xml".format(nodepathlib.get_leaf_name(node))
			file_path = os.path.join(directory, file_name)

			# do export
			io = cls(node)
			io.export_weights(file_path, deformer_types, remove_namespaces)

	# ------------------------------------------------------------------------

	def import_weights(self, file_path, deformer_types=None, method="index", set_attributes=False):
		"""
		Import the deformer weights from the xml dataexporter. It uses the standard
		functionality of the cmds.deformerWeights function.

		:param str file_path:
		:param str/list/None deformer_types:
		:param str method: "index", "nearest", "barycentric", "bilinear" or "over"
		:param bool set_attributes:
		"""
		# validate path
		if not os.path.exists(file_path):
			error_message = "File path '{}' doesn't exist on disk!".format(file_path)
			log.error(error_message, exc_info=1)
			raise OSError(error_message)

		# get directory and file name
		directory, file_name = os.path.split(file_path)

		# get xml
		self.xml = DeformerWeightsXML.load(file_path)

		# filter deformer types
		deformer_types = utilslib.conversion.as_list(deformer_types)

		# read xml file
		deformer_data = self.extract_xml_deformer_data(deformer_types)

		for deformer_name, deformer_dict in deformer_data.items():
			# validate deformer
			if not cmds.objExists(deformer_name):
				# if the deformer name doesn't match, we will find any
				# existing deformers of the specified node type on the node.
				# if only one match exist we assume
				deformers = self.get_deformers(deformer_dict.get("type"))
				if len(deformers) != 1:
					log.warning("Skipped deformer '{}', it doesn't exist!".format(deformer_name))
					continue

				deformer_name = deformers[0]

			# set deformer weights
			cmds.deformerWeights(
				file_name,
				shape=self.node_shape,
				path=directory,
				method=method,
				im=True,
				deformer=deformer_name,
			)

			# set deformer attributes
			if set_attributes:
				self.set_deformer_attributes(deformer_name, deformer_dict.get("attributes"))

			log.info(
				"Imported '{}' deformer weights from '{}' onto node '{}'".format(
					deformer_name,
					file_path,
					self.node
				)
			)

	@classmethod
	def import_weights_multi(cls, nodes, directory, deformer_types=None, method="index", set_attributes=False):
		"""
		Import the deformer weights from the xml dataexporter. It uses the standard
		functionality of the cmds.deformerWeights function. All nodes will be
		looped and have their deformer weights imported.

		:param list nodes:
		:param str directory:
		:param str/list/None deformer_types:
		:param str method: "index", "nearest", "barycentric", "bilinear" or "over"
		:param bool set_attributes:
		"""
		for node in nodes:
			try:
				# get file name
				file_name = "{}.xml".format(nodepathlib.get_leaf_name(node))
				file_path = os.path.join(directory, file_name)

				# do import
				io = cls(node)
				io.import_weights(file_path, deformer_types, method, set_attributes)
			except OSError:
				pass
