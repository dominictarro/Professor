"""

Contains classes and functions to construct session types

"""
from typing import Union, Dict, Callable, Any
from discord.ext import commands
import discord

from prof.utils.numeric import Time
from prof.utils.event import on_change_embed


class SessionBase(object):

	def __init__(self, *args, **kwargs):
		"""
		Abstract class for managing events and callbacks to quizzes.

		:param quiz:    Quiz session is managing
		:param context: Discord context
		:param users:   Dictionary matching user id's to User objects
		"""
		self.quiz = None
		self.context = None
		self.build(*args, **kwargs)

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting parameters on initialization

		:return:
		"""
		self.__dict__.update(kwargs)

	def on_message(self, message: discord.Message):
		"""
		Placeholder method for a specific session's callback on a message

		:param message:
		:return:
		"""
		pass

	def on_react(self, reaction: discord.Reaction, user: discord.User):
		"""
		Placeholder method for a specific session's callback on a reaction

		:param reaction:    The specific reaction
		:param user:        The user who reacted
		:return:
		"""


class PrivateSession(object):

	def __init__(self, *args, **kwargs):
		"""
		Abstract class for developing session spaces where a user is being handled independent of any other.

		:param args:
		:param kwargs:
		"""
		super(PrivateSession, self).__init__(*args, **kwargs)


class SharedSession(object):

	def __init__(self, *args, **kwargs):
		"""
		Abstract class for developing sessions where multiple users are being handled at once.

		:param args:
		:param kwargs:
		"""
		self.users: Dict[int, Any] = {}
		super(SharedSession, self).__init__(*args, **kwargs)

	def __getitem__(self, id: int):
		return self.users[id]


class QuizSession(SessionBase):

	def __init__(self, *args, **kwargs):
		"""
		Class for overseeing quiz administration and pre/post processing

		:param args:
		:param kwargs:
		"""
		self.period = Time(minutes=1)
		super(QuizSession, self).__init__(*args, **kwargs)


class EditSession(SessionBase):
	_bool_map = {"true": True, "false": False}
	_quiz_str_max_len = 50

	def __init__(self, *args, **kwargs):
		"""
		Class for overseeing quiz editing and pre/post processing

		:param args:
		:param kwargs:
		"""
		super(EditSession, self).__init__(*args, **kwargs)

	def edit_quiz_boolean(self, change: str, attribute: str):
		"""
		Edits the value of a boolean attribute in the quiz

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if (change := change.lower()) in self._bool_map:
			self.quiz.__dict__[attribute] = self._bool_map[change]
			return True
		return False

	def edit_question_boolean(self, i: int, change: str, attribute: str):
		"""
		Edits the value of a boolean attribute in a question

		:param i:           Question's index
		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if (change := change.lower()) in self._bool_map:
			self.quiz[i].__dict__[attribute] = self._bool_map[change]
			return True
		return False

	def edit_quiz_numeric(self, change: str, attribute: str):
		"""
		Edits the value of a numeric attribute in the quiz

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if change.isnumeric():
			self.quiz.__dict__[attribute] = int(change)
			return True
		else:
			parts = change.split('.')
			if all(x.isnumeric() for x in parts) & len(parts) == 2:
				self.quiz.__dict__[attribute] = float(change)
				return True
		return False

	def edit_question_numeric(self, i: int, change: str, attribute: str):
		"""
		Edits the value of a numeric attribute in the quiz

		:param i:           Question's index
		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if change.isnumeric():
			self.quiz[i].__dict__[attribute] = int(change)
			return True
		else:
			parts = change.split('.')
			if all(x.isnumeric() for x in parts) & len(parts) == 2:
				self.quiz[i].__dict__[attribute] = float(change)
				return True
		return False

	def edit_quiz_string(self, change: str, attribute: str):
		"""
		Edits the value of a string attribute in the quiz

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if 0 < len(change) <= self._quiz_str_max_len:
			self.quiz.__dict__[attribute] = change
			return True
		return False

	def edit_question_string(self, i: int, change: str, attribute: str):
		"""
		Edits the value of a string attribute in a question

		:param i:           Question's index
		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if 0 < len(change) <= self._quiz_str_max_len:
			self.quiz[i].__dict__[attribute] = change
			return True
		return False


