from typing import Union, Dict, Callable, Any

from prof.utils.numeric import Time


class QuizBase(object):

	def __int__(self, *args, **kwargs):
		"""
		:param name:        Name given by quiz creator
		:param id:          Identifier in database
		:param shuffle:     Whether to randomize question order
		:param questions:   All questions in quiz
		:param size:        How many questions to sample and administer

		:return:
		"""
		self.name: str = ""
		self.id: int = 0
		self.shuffle: bool = True
		self.questions: list = []
		self.size: Union[int, str] = '*'
		self._limit: Time = Time(minutes=10)
		self.build()

	@property
	def limit(self):
		return self._limit

	@limit.setter
	def limit(self, new: Time):
		pass

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting parameters on initialization

		:return:
		"""
		self.__dict__.update(kwargs)


class SyncQuiz(QuizBase):

	def __init__(self, *args, **kwargs):
		super(SyncQuiz, self).__init__(*args, **kwargs)

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting parameters on initialization

		:return:
		"""
		self.__dict__.update(kwargs)


class AsyncQuiz(QuizBase):

	def __init__(self, *args, **kwargs):
		super(AsyncQuiz, self).__init__(*args, **kwargs)

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting parameters on initialization

		:return:
		"""
		self.__dict__.update(kwargs)
