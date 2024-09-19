import logging

import maya.cmds as cmds

from smrig.lib.constraintslib import common as constraint_

log = logging.getLogger("smrig.lib.constraintslib.alias")


def set_weight_aliases(constraint, values):
	"""
	Sets the values on the targets weight attributes of a constraint.
	The number of values  should match the number of targets in on the constraint.

	:param str constraint:
	:param list values: In order target weight influences
	:raise ValueError:
		When the number of aliases don't match up with the number of values
	"""
	# get aliases and values
	aliases = get_weight_aliases(constraint, node_path=True)

	# validate aliases and values
	num_aliases = len(aliases)
	num_values = len(values)
	if num_aliases != num_values:
		error_message = "Number of aliases '{}' doesn't match the number of values '{}'.".format(
			num_aliases,
			num_values
		)

		log.error(error_message)
		raise ValueError(error_message)

	# set values
	for alias, value in zip(aliases, values):
		cmds.setAttr(alias, value)


def get_weight_aliases(constraint, node_path=False):
	"""
	Returns the name of the target weight attributes of a given constraint.

	Example:
		.. code-block:: python

			names = get_weight_aliases(constraint='L_leg_001_PAC')
			>> ['C_spine_001_CTLW0', 'C_neck_003_CTLW1', ...]

			names = get_weight_aliases(constraint='L_leg_001_PAC', node_path=True)
			>> ['L_fingerA_01_pac_GRP_parentConstraint1.L_arm_006_JNTW0', ...]

	:param str constraint:
	:param bool node_path: Returns either just the target names or the full node path.
	:return: A list of either the short or long names of the target attribute names
	:rtype: list
	"""
	constraint_type = cmds.nodeType(constraint)
	constraint_func = constraint_.get_constraint_command(constraint_type)

	aliases = constraint_func(constraint, query=True, weightAliasList=True)
	aliases = aliases if not node_path else ["{}.{}".format(constraint, a) for a in aliases]

	return aliases
