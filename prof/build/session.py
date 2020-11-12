"""

Contains classes and functions to construct session types

"""
from typing import Union, Dict, Callable, Any, Optional
from discord.ext import commands
import datetime
import discord

from prof.build.quiz import Quiz
from prof.utils.numeric import Time


class SessionBase(object):

	def __init__(self, _id: int, *args, **kwargs):
		"""
		Abstract class for managing events and callbacks to quiz objects.

		:param quiz:    Quiz session is managing
		:param context: Discord context
		-----------------------------------------------------------
		Subclass parameters
		:param user:    An individual user being handled
		:param users:   A dictionary of users being handled (user id: private session)

		"""
		self.quiz: Optional[Quiz] = None
		self.context: Optional[commands.Context] = None
		self.id: int = _id

		assert "quiz" in kwargs
		self.__dict__.update(kwargs)
		self.build(*args, **kwargs)

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting parameters on initialization

		:return:
		"""

	def close(self):
		"""
		Placeholder method for the session's closing process

		:return:
		"""

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


class PublicSession(SessionBase):

	def __init__(self, *args, **kwargs):
		"""
		Abstract class for developing sessions where multiple users are being handled at once. Each user
		is directly interacted with via a private session.

		:param users: dictionary matching Discord user ID to Discord user object

		:param args:
		:param kwargs:
		"""
		self.users: Dict[int, PrivateSession] = {}
		super(PublicSession, self).__init__(*args, **kwargs)
		self.build(*args, **kwargs)

	def __getitem__(self, id: int):
		return self.users[id]

	def build(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""


class PublicQuizSession(PublicSession):

	def __init__(self, *args, **kwargs):
		"""
		Abstract class for publicly hosting quizzes

		:param open_time:       The time this session was initiated
		:param close_time:      The time this session will close
		:param kill_on_period:  Close all private sessions when period ends

		:param args:
		:param kwargs:
		"""
		self.open_time = datetime.datetime.utcnow()
		self.period: Time = Time(minutes=10)
		self.kill_on_period: bool = True
		super(PublicQuizSession, self).__init__(*args, **kwargs)
		self.close_time = self.open_time + datetime.timedelta(**self.period.dict)
		self.users: Dict[int, PrivateQuizSession] = {}

	def build(self, *args, **kwargs):
		"""

		:param args:
		:param kwargs:
		:return:
		"""

	def kill(self):
		"""
		Base script for terminating all sessions.

		:return:
		"""
		for priv_sesh in self.users.values():
			priv_sesh.close()

	def close(self):
		"""
		Base script for closing

		:return:
		"""
		self.kill()

	def create_private_quiz(self, user: discord.User):
		"""
		Creates a private quiz session.

		:param user:
		:return:
		"""
		self.users[user.id] = PrivateQuizSession(parent=self, _id=user.id, quiz=self.quiz, user=user)


class PrivateSession(SessionBase):

	def __init__(self, user: discord.User, *args, **kwargs):
		"""
		Abstract class for developing session spaces where a user is being handled independent of any other.


		:param args:
		:param kwargs:
		"""
		self.user: discord.User = user
		self.active: bool = True
		super(PrivateSession, self).__init__(*args, **kwargs)

	def build(self, *args, **kwargs):
		"""
		Takes a set of arguments and constructs the session object

		:param args:
		:param kwargs:
		:return:
		"""

	def on_message(self, message: discord.Message):
		"""
		Callback for when the user sends a message.

		:param message:
		:return:
		"""
		# TODO: add check statement

	def on_react(self, reaction: discord.Reaction, user: discord.User = None):
		"""
		Callback for when the user reacts to a message

		:param reaction:    The specific reaction
		:param user:        Only here to satisfy base method signature. User already known to private session object
		:return:
		"""
		# TODO: add check statement


class PrivateQuizSession(PrivateSession):

	def __init__(self, parent: PublicQuizSession, *args, **kwargs):
		"""
		Class for overseeing quiz administration and pre/post processing

		:param args:
		:param kwargs:
		"""
		self.parent: PublicQuizSession = parent
		self.time_taken: Time = Time()
		super(PrivateQuizSession, self).__init__(*args, **kwargs)

	@property
	def time_remaining(self):
		"""
		Creates a Time object to represent the remaining time.

		:return:
		"""
		remaining = self.quiz.limit - self.time_taken
		if self.parent.kill_on_period:
			# If kill_on_period, the remaining time is the minimum between the parent session ending
			# and the remaining time on the quiz (time limit - time lapsed)
			until_period_end = self.parent.close_time - datetime.datetime.utcnow()
			return min(remaining, Time.from_timedelta(until_period_end))
		# If not kill_on_period, only consider the time the user has taken
		return remaining


class PrivateEditSession(PrivateSession):

	def __init__(self, *args, **kwargs):
		"""
		Class for overseeing quiz editing and pre/post processing

		:param args:
		:param kwargs:
		"""
		super(PrivateEditSession, self).__init__(*args, **kwargs)


period = Time(weeks=1, days=1, seconds=1)
x = datetime.timedelta(**period.dict)
print(x)
print(Time.from_timedelta(x))

