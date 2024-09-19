import logging
from functools import partial

log = logging.getLogger("smrig.lib.utilslib.ssm")


class TransitionError(Exception):
	"""
	The transition error is a custom exception that is raised by the
	SimpleStateMachine class when a transition cannot be made.

	:param str message:
	"""

	def __init__(self, message):
		super(TransitionError, self).__init__(message)


class Transition(object):
	"""
	The transition class stores the original function and name before
	overwriting call. It also contains the allowed transitions the amount of
	times the function has been called. This can be help full to determine if
	the transition is allowed.
	"""

	def __init__(self, func):
		self._func = func
		self._name = func.__name__
		self._transitions = []
		self._calls = 0
		self._allow_cycle = False

	# ------------------------------------------------------------------------

	@property
	def name(self):
		"""
		:return: Name
		:rtype: str
		"""
		return self._name

	@property
	def calls(self):
		"""
		:return: Function calls
		:rtype: int
		"""
		return self._calls

	# ------------------------------------------------------------------------

	@property
	def allow_cycle(self):
		"""
		:param bool state:
		:return: Allow cycle
		:rtype: bool
		"""
		return self._allow_cycle

	@allow_cycle.setter
	def allow_cycle(self, state):
		self._allow_cycle = state

	# ------------------------------------------------------------------------

	@property
	def transitions(self):
		"""
		:return: Transition names
		:rtype: list
		"""
		return self._transitions

	def add_transition(self, name):
		"""
		:param str name:
		"""
		if name not in self.transitions:
			self.transitions.append(name)

	def remove_transition(self, name):
		"""
		:param str name:
		"""
		if name in self.transitions:
			self.transitions.remove(name)

	# ------------------------------------------------------------------------

	def run(self, *args, **kwargs):
		ret = self._func(*args, **kwargs)
		self._calls += 1

		return ret


class SimpleStateMachine(object):
	"""
	Simple state machine that will prevent function from being ran if the it
	is not part of the transition the current state is allowed to make. Once
	a function is ran the name of that function becomes the new state. This
	way it will be easy to alert the user when running functions out of order.
	Ideal to be used when multiple functions can be ran to get a more or less
	identical output which then can be used in other functions. Making it
	easier and more visible to implement a greater variety of solutions using

	The simple state machine doesn't require an init to be ran meaning it can
	be used as a mixin.

	Example
		.. code-block:: python

			class Test(SimpleStateMachine):
				def __init__(self):
					super(Test, self).__init__()
					self.create_transitions("__init__", "func1", allow_cycle=False)
					self.create_transitions("func1", "func3")
				def func1(self, value=None):
					print ("func1", value)
				def func2(self):
					print ("func2")
				def func3(self):
					print ("func3")

				def func4(self):
					print ("func4")
			t = Test()
			t.func1("test")
			t.func2()
			# TransitionError: Cannot transition to state 'func2' as the ...
	"""
	_state = "__init__"
	_transitions = None

	@property
	def state(self):
		"""
		:return: Current state
		:rtype: str/None
		"""
		return self._state

	@property
	def transitions(self):
		"""
		:return: All transitions
		:rtype: dict
		"""
		if self._transitions is None:
			self._transitions = {}

		return self._transitions

	# ------------------------------------------------------------------------

	def check_transition(self, transition, *args, **kwargs):
		"""
		Decorator function that checks to see if the function called is
		allowed to run based on the current state. If this is not the case a
		TransitionError will be raised stating the current state and the
		transitions allowed.

		When the function has ran the state will be updated with the name of
		the function.

		:param str transition:
		"""
		# get transition dataexporter
		state = self.transitions.get(self.state)
		transition = self.transitions.get(transition)

		# validate transition
		if transition.name not in state.transitions:
			raise TransitionError(
				"Cannot transition to state '{}' as the current state "
				"'{}' only allows transition to {}.".format(
					transition.name,
					self.state,
					state.transitions
				)
			)

		# validate transition
		if transition.calls and not transition.allow_cycle:
			raise TransitionError(
				"Cannot transition to state '{}' as at has already been "
				"called and it doesn't allow cycling.".format(
					transition.name,
				)
			)

		# call function
		ret = transition.run(*args, **kwargs)

		# update state
		self._state = transition.name

		return ret

	# ------------------------------------------------------------------------

	def create_transition(self, state, transition):
		"""
		Create transitions linked to a state. It means that from the provided
		state the transitions provided are allowed.

		:param str state:
		:param str transition:
		:raise ValueError: When the state doesn't exist in the class.
		:raise ValueError: When the transition doesn't exist in the class.
		"""
		# validate transition
		for prefix, func_name in zip(["State", "Transition"], [state, transition]):
			if func_name not in dir(self):
				raise ValueError(
					"{} '{}' doesn't exist in the class.".format(
						prefix,
						transition
					)
				)

		# add state
		if state not in self.transitions:
			func = getattr(self, state)
			self.transitions[state] = Transition(func)

		# add transition
		if transition not in self.transitions:
			func = getattr(self, transition)
			self.transitions[transition] = Transition(func)
			setattr(self, transition, partial(self.check_transition, transition))

		# add transition
		data = self.transitions[state]
		data.add_transition(transition)

	def remove_transition(self, state, transition):
		"""
		Remove a transition from the provided state. This can be done on the
		fly to alter the transitions in current code. There can be edge cases
		where certain transitions are invalid based on the code ran. This
		function can be used to alter this behaviour and can be used outside
		the init.

		:param str state:
		:param str transition:
		:raise ValueError: When the state doesn't exist in the transitions.
		:raise ValueError: When the transition doesn't exist in the transitions.
		"""
		# validate transition
		for prefix, func_name in zip(["State", "Transition"], [state, transition]):
			if not self.transitions.get(func_name):
				raise ValueError(
					"{} '{}' doesn't exist in the transition.".format(
						prefix,
						transition
					)
				)

		# remove transition
		state = self.transitions.get(state)
		transition = self.transitions.get(transition)
		state.remove_transition(transition.name)

	def edit_transition(self, state, allow_cycle=None):
		"""
		Edit a transition func. This function will allow you to add special
		conditions to a function.

		:param str state:
		:param bool allow_cycle:
		:raise RuntimeError: When state is not defined in the transitions.
		"""
		# validate state
		if state not in self.transitions:
			error_message = "State '{}' is not part of the transitions.".format(state)
			log.error(error_message)
			raise RuntimeError(error_message)

		# get transition
		transition = self.transitions[state]

		# edit attributes
		if allow_cycle is not None:
			transition.allow_cycle = allow_cycle
