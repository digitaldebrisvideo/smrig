# import lxml.etree as etree
import logging

from smrig.lib import nodepathlib

log = logging.getLogger("smrig.lib.deformlib.xml")


class DeformerWeightsXML(object):
	"""
	The deformer xml class helps find and edit information relating the
	deformer weights. It is possible to easily have access to the deformers
	its attribute and weights using utility functions. All functions used
	to read dataexporter will return xml objects which can be used to further query
	any dataexporter necessary.

	The class is designed to only help with reading and editing of the xml
	file. Any conversion from XML to a format more usable will have to happen
	outside of this class.

	Example:
		.. code-block:: python

			# initialize class
			deformer_xml = DeformerWeightsXML.load(file_path)

			# get all deformers
			print deformer_xml.get_deformers()

			# change deformer name
			deformer_xml.rename_deformer("skinCluster1", "C_body_PLY_SKN")

			# change weight source name
			deformer_xml.rename_weights_source("L_IndexFinger1FK_JNT", "L_IndexFinger1_JNT")

			# save changes
			deformer_xml.save()

	:param str file_path:
	"""

	def __init__(self, file_path):
		self._file_path = file_path

		# read xml file
		tree = etree.parse(file_path)
		self._root = tree.getroot()

	# ------------------------------------------------------------------------

	@property
	def file_path(self):
		"""
		:return: File path to xml
		:rtype: str
		"""
		return self._file_path

	# ------------------------------------------------------------------------

	def get_shape(self):
		"""
		:return: Shape
		:rtype: lxml.etree._Element
		"""
		return self._root.find("shape")

	# ------------------------------------------------------------------------

	def get_deformer(self, deformer):
		"""
		:param str deformer:
		:return: Deformer
		:rtype: lxml.etree._Element/None
		"""
		deformer_objs = self._root.xpath('//deformer[@name="{}"]'.format(deformer))
		if not deformer_objs:
			error_message = "Deformer '{}' not found in the xml!".format(deformer)
			log.error(error_message, exc_info=1)
			raise ValueError(error_message)

		return deformer_objs[0]

	def get_deformers(self):
		"""
		:return: Deformers
		:rtype: dict
		"""
		return {
			deformer.get("name"): deformer
			for deformer in self._root.findall("deformer")
		}

	def rename_deformer(self, source, target):
		"""
		This will change the deformer name on the xml objects. If you would
		like to make sure that this change is reflected in the file it is
		important to save it. The change will be reflected in the class.

		Example:
			.. code-block:: python

				deformer_xml = DeformerWeightsXML.load(file_path)
				deformer_xml.rename_deformer("skinCluster1", "C_body_PLY_SKN")
				deformer_xml.save()

		:param str source:
		:param str target:
		"""
		# change deformer name
		deformer = self.get_deformer(source)
		deformer.set("name", target)

		# change weights associated with deformer
		for weights in self.get_deformer_weights(source):
			weights.set("deformer", target)

	# ------------------------------------------------------------------------

	def get_deformer_attributes(self, deformer):
		"""
		:param str deformer:
		:return: Deformer attributes
		:rtype: list
		"""
		deformer = self.get_deformer(deformer)
		return deformer.findall("attribute")

	def get_deformer_weights(self, deformer):
		"""
		:param str deformer:
		:return: Deformer weights
		:rtype: list
		"""
		return self._root.xpath('//weights[@deformer="{}"]'.format(deformer))

	# ------------------------------------------------------------------------

	def rename_weights_source(self, source, target):
		"""
		The weight source varies based on deformer. The most likely use case
		for this command is to change the influence names of the joints when
		having exported skin weights.

		Example:
			.. code-block:: python

				deformer_xml = DeformerWeightsXML.load(file_path)
				deformer_xml.rename_weights_source("L_IndexFinger1FK_JNT", "L_IndexFinger1_JNT")
				deformer_xml.save()

		:param str source:
		:param str target:
		"""
		weights_objs = self._root.xpath('//weights[@source="{}"]'.format(source))
		if not weights_objs:
			error_message = "Weights Source '{}' not found in the xml!".format(source)
			log.error(error_message, exc_info=1)
			raise ValueError(error_message)

		for weights_obj in weights_objs:
			weights_obj.set("source", target)

	# ------------------------------------------------------------------------

	def remove_namespaces(self):
		"""
		Remove any namespaces from the deformer names and the weights source
		names. Ideal for when exporting from a shot with references.
		"""
		for deformer in self.get_deformers().keys():
			# rename weight source
			for weight in self.get_deformer_weights(deformer):
				name = weight.get("source")
				self.rename_weights_source(
					name,
					nodepathlib.get_leaf_name(name)
				)

			# rename deformer
			self.rename_deformer(
				deformer,
				nodepathlib.get_leaf_name(deformer)
			)

	# ------------------------------------------------------------------------

	def save(self, overwrite_file_path=None):
		"""
		Save the xml file, by default the file will overwrite the file path
		used to initialize the command. For safety reasons it is possible to
		save the file to a different location.

		:param str overwrite_file_path:
		"""
		file_path = overwrite_file_path if overwrite_file_path else self.file_path
		tree = etree.ElementTree(self._root)
		tree.write(file_path)

	@classmethod
	def load(cls, file_path):
		"""
		:param str file_path:
		:return: Deformer XML
		:rtype: :class:`~DeformerWeightsXML`
		"""
		return cls(file_path)
