import maya.cmds as cmds

from smrig.lib import utilslib


class DisableAutoKeyframe(object):
	"""
	When moving controls around in an animated scene it can be useful to make
	sure that auto key is turned off. Otherwise you'd unknowingly edit the
	animation.
	"""

	def __init__(self):
		self._state = cmds.autoKeyframe(query=True, state=True)

	def __enter__(self):
		if self.state:
			cmds.autoKeyframe(state=False)

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.state:
			cmds.autoKeyframe(state=self.state)

	# ------------------------------------------------------------------------

	@property
	def state(self):
		"""
		:return: Auto keyframe state
		:rtype: bool
		"""
		return self._state


def set_driven_key_multi(sdk_data, in_tangent_type="auto", out_tangent_type="auto"):
	"""
	Use a list of driver and driven values to set up lots of set driven keys
	at once. It is assumed that the driven_key_data argument is a list of
	lists where the internal list reflects the driver, driver_value, driven
	and driven_value to be set as a set driven keyframe. These set driven key
	values are set using the :meth:`~set_driven_key` function.

	The optional values for the in and out tangents are; "auto", "clamped",
	"fast", "flat", "linear", "plateau", "slow", "spline", "step" and
	"stepnext"

	Example:
		.. code-block:: python

			sdk_data = [
				[driver.channel, driverValue, driven.channel, drivenValue],
				[driver.channel, driverValue, driven.channel, drivenValue],
				[driver.channel, driverValue, driven.channel, drivenValue],
			]

			set_driven_key_dict(sdk_data)

	:param list sdk_data:
	:param str in_tangent_type:
	:param str out_tangent_type:
	"""
	for driver, driver_value, driven, driven_value in sdk_data:
		set_driven_key(
			driver=driver,
			driver_value=driver_value,
			driven=driven,
			driven_value=driven_value,
			in_tangent_type=in_tangent_type,
			out_tangent_type=out_tangent_type,
		)


def set_driven_key(driver, driver_value, driven, driven_value, in_tangent_type="linear", out_tangent_type="linear"):
	"""
	Shorter wrapper for cmds.setDrivenKey command. The optional values for the
	in and out tangents are; "auto", "clamped", "fast", "flat", "linear",
	"plateau", "slow", "spline", "step" and "stepnext"

	Example:
		.. code-block:: python

			set_driven_key(
				driver='L_leg_001_CTL.ikFk',
				driver_value=0,
				driven='L_leg_001_ikFkSwitch_REV.inputX',
				driven_value=1,
				in_tangent_type="linear",
				out_tangent_type="linear"
			)


	:param str driver: Driver attribute path
	:param float/int driver_value:
	:param str driven: Driven attribute path
	:param float/int driven_value:
	:param str in_tangent_type:
	:param str out_tangent_type:
	"""
	cmds.setDrivenKeyframe(
		driven,
		currentDriver=driver,
		driverValue=driver_value,
		value=driven_value,
		inTangentType=in_tangent_type,
		outTangentType=out_tangent_type
	)


def get_anim_curves(node, sdk_only=False):
	"""

	:param node:
	:param sdk_only:
	:return:
	"""
	bws = cmds.listConnections(node, type="blendWeighted", scn=True) or []
	crvs = cmds.listConnections(utilslib.conversion.as_list(node) + bws, type="animCurve", scn=True) or []

	if sdk_only:
		return [s for s in crvs if cmds.listConnections(s + ".input", s=True, d=False)]
	else:
		return crvs


def set_inifity(curves, pre="linear", post="linear"):
	"""
	Set infinity on curves

	:param curves:
	:param pre:
	:param post:
	:return:
	"""
	cmds.selectKey(curves)
	cmds.setInfinity(pri=pre, poi=post)


def set_tangent_type(curves, itt="linear", ott=None):
	"""
	Set all keys on curves to specified tanget.

	:param curves:
	:param str itt: auto, spline, clamped, linear, flat, step, plateau
	:param str ott: auto, spline, clamped, linear, flat, step, plateau
	:return:
	"""
	ott = ott if ott else itt
	cmds.selectKey(curves)
	cmds.keyTangent(itt=itt, ott=ott)
