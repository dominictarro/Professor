from typing import Union, Dict, Callable, Any
import random

from professor.utils.numeric import Time


class Quiz(object):

	_bool_map = {"true": True, "false": False}
	__kwarg_map = dict(period="_period", limit="_limit")

	def __init__(self, *args, **kwargs):
		"""
		:param name:        Name given by quiz creator
		:param id:          Identifier in database
		:param shuffle:     Whether to randomize question order
		:param questions:   All questions in quiz
		:param size:        How many questions to sample and administer

		:param sample:      A sample of questions to administer
		:return:
		"""
		self.name: str = ""
		self.id: int = 0
		self.shuffle: bool = True
		self.questions: list = []
		self.size: Union[int, str] = '*'
		self._limit: Time = Time(minutes=10)
		self._period: Time = Time(minutes=1)

		kwargs = self.__kwarg_filter(**kwargs)
		self.__dict__.update(kwargs)
		self.size = len(self.questions) if self.size == '*' else self.size

	@property
	def limit(self):
		return self._limit

	@limit.setter
	def limit(self, new: Time):
		assert isinstance(new, Time) & (new <= Time(weeks=1))
		self._limit = new

	def __iter__(self):
		"""
		Generator for a sample of questions of the given size

		:return:
		"""
		yield from random.sample(self.questions, k=self.size)

	def __kwarg_filter(self, **kwargs):
		"""
		Method for renaming keywords on initialization and removing unsupported keywords

		:return:
		"""
		for k, v in kwargs.items():
			if k in self.__kwarg_map:
				# Rename key
				kwargs[self.__kwarg_map[k]] = v
			elif k not in self.__dict__:
				# Drop unsupported keywords
				kwargs.pop(k)

		return kwargs

	def edit_boolean(self, change: str, attribute: str):
		"""
		Edits the value of a boolean attribute in the quiz

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if (change := change.lower()) in self._bool_map:
			self.__dict__[attribute] = self._bool_map[change]
			return True
		return False

	def edit_numeric(self, change: str, attribute: str):
		"""
		Edits the value of a numeric attribute in the quiz

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		if change.isnumeric():
			self.__dict__[attribute] = int(change)
			return True
		else:
			parts = change.split('.')
			if all(x.isnumeric() for x in parts) & (0 < len(parts) < 3):
				self.__dict__[attribute] = float(change)
				return True
		return False


if __name__ == "__main__":
	quiz = Quiz(questions=["a", "b", "c"])
	print(quiz.questions)
	for x in quiz:
		print(x)
