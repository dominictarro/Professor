"""

Classes, functions, etc. that deal mostly with computation

"""

from typing import Optional, Union, Dict, Tuple, Callable
import datetime
import re


def auto_simplify(f: Callable) -> Callable:
	"""

	:param f:
	:return:
	"""
	def wrap(inst, *args, **kwargs):
		x = f(inst, *args, **kwargs)
		x.simplify()
		return x
	return wrap


class Time(object):

	__units = ("weeks", "days", "hours", "minutes", "seconds")

	def __init__(self,
				 seconds: Optional[Union[int, float]]=0,
				 minutes: Optional[Union[int, float]]=0,
				 hours: Optional[Union[int, float]]=0,
				 days: Optional[Union[int, float]]=0,
				 weeks: Optional[Union[int, float]]=0,
				 round: Optional[int] = None
	):
		"""
		Object representing time and capable of parsing the format
		weeks:days:hours:minutes:seconds

		:param seconds: ...
		:param minutes: ...
		:param hours:   ...
		:param days:    ...
		:param weeks:   ...
		:param round:   How many places to round the seconds to
		"""
		assert all(x >= 0 for x in (seconds, minutes, hours, days, weeks))
		self.days = days
		self.hours = hours
		self.minutes = minutes
		self.seconds = seconds
		self.weeks = weeks
		self.round = round

	@auto_simplify
	def __new__(cls, *args, **kwargs):
		inst = object.__new__(cls)
		inst.__init__(*args, **kwargs)
		return inst

	@property
	def as_seconds(self) -> Union[int, float]:
		return self.seconds + 60*(self.minutes + 60*(self.hours + 24*(self.days + 7*self.weeks)))

	@classmethod
	def parse(cls, string: str, round: Optional[int] = 0):
		"""
		Converts a colon-separated string into a time, prioritizing the lowest time.

		e.g. 1:30 is 1 minute and 30 seconds
		e.g. 10:0:0:0 is 1 week and 3 days

		:param string:
		:return:
		"""
		t = Time(round=round)
		splits = re.split('[:]', string)
		for i, unit in enumerate(cls.__units[-len(splits):]):
			if splits[i].isnumeric():
				t.__dict__[unit] = int(splits[i])
			elif all(x.isnumeric() for x in splits[i].split('.')):
				t.__dict__[unit] = float(splits[i])
		return t

	@classmethod
	def from_timedelta(cls, dt: datetime.timedelta):
		"""
		Converts a datetime object to a Time object

		:param dt:
		:return:
		"""
		return Time(days=dt.days, seconds=dt.seconds)

	@staticmethod
	def unit_string(x: Union[float, int], name: str) -> Optional[str]:
		"""
		Converts a unit of time to a string

		:param x:       unit's value
		:param name:    unit's name (singular)
		:return:
		"""
		if x > 0:
			if x == 1:
				return f"1 {name}"
			return f"{x} {name}s"

	def __str__(self):
		"""
		Converts time to legible string for display

		:return:
		"""
		concat = []
		units = [
			(self.weeks, "week"),
			(self.days, "day"),
			(self.hours, "hour"),
			(self.minutes, "minute"),
			(self.seconds, "second")
		]
		for x, name in units:
			string = self.unit_string(x=x, name=name)
			if string:
				concat.append(string)
		if len(concat) == 1:
			return concat[0]
		elif len(concat) == 0:
			return "0 seconds"
		return ', '.join(concat[:-1]) + " and " + concat[-1]

	def __repr__(self):
		"""
		Object representation
		:return:
		"""
		return f"Time({' '.join(f'{name}={self.__dict__[name]}' for name in self.__units if self.__dict__[name])})"

	def __ge__(self, x):
		assert isinstance(x, Time)
		return self.as_seconds >= x.as_seconds

	def __gt__(self, x):
		assert isinstance(x, Time)
		return self.as_seconds > x.as_seconds

	def __le__(self, x):
		assert isinstance(x, Time)
		return self.as_seconds <= x.as_seconds

	def __lt__(self, x):
		assert isinstance(x, Time)
		return self.as_seconds < x.as_seconds

	def __eq__(self, x):
		assert isinstance(x, Time)
		return self.as_seconds == x.as_seconds

	@auto_simplify
	def __add__(self, x):
		assert isinstance(x, Time)
		return Time(seconds=self.as_seconds + x.as_seconds)

	@auto_simplify
	def __radd__(self, x):
		assert isinstance(x, Time)
		return Time(seconds=self.as_seconds + x.as_seconds)

	@auto_simplify
	def __sub__(self, x):
		assert isinstance(x, Time)
		return Time(seconds=self.as_seconds - x.as_seconds)

	@auto_simplify
	def __rsub__(self, x):
		assert isinstance(x, Time)
		return Time(seconds=x.as_seconds - self.as_seconds)

	@auto_simplify
	def __mul__(self, x: Union[int, float]):
		return Time(seconds=self.as_seconds * x)

	@auto_simplify
	def __rmul__(self, x: Union[int, float]):
		return Time(seconds=self.as_seconds * x)

	@auto_simplify
	def __truediv__(self, x: Union[int, float]):
		return Time(seconds=self.as_seconds / x)

	@auto_simplify
	def __rtruediv__(self, x: Union[int, float]):
		return Time(seconds=x / self.as_seconds)

	@property
	def dict(self):
		"""
		A dictionary representation of the time

		:return:
		"""
		return {k: self.__dict__[k] for k in self.__units}

	def simplify(self):
		"""
		Simplifies time based on time rules
		seconds < 60
		minutes < 60
		hours   < 24
		days    < 7

		:return:
		"""
		self.__smooth_backward()
		if self.round is not None:
			self.seconds = round(self.seconds, self.round) if self.round != 0 else int(round(self.seconds, self.round))
		self.__smooth_forward()
		# Enforce integer type after smoothing for all units but seconds
		for unit in self.__units[:-1]:
			self.__dict__[unit] = int(self.__dict__[unit])

	@staticmethod
	def __integer_extract(x: Union[float, int]) -> Tuple[int, float]:
		"""
		Takes a value and creates a sum between an integer component and decimal

		:param x:
		:return:
		"""
		n, d = x.as_integer_ratio()
		part_sum = n % d / d
		extract = int(x - part_sum)
		return extract, part_sum

	def __smooth_backward(self):
		"""
		Pushes fractional time towards the smaller unit of time based on time rules

		seconds < 60
		minutes < 60
		hours   < 24
		days    < 7

		:return:
		"""
		self.weeks, lay = self.__integer_extract(self.weeks)
		self.days += lay*7

		self.days, lay = self.__integer_extract(self.days)
		self.hours += lay*24

		self.hours, lay = self.__integer_extract(self.hours)
		self.minutes += lay*60

		self.minutes, lay = self.__integer_extract(self.minutes)
		self.seconds += lay*60

	def __smooth_forward(self):
		"""
		Pushes excess time in each category into the larger unit of time based on time rules
		e.g. 25 hours -> 1 day 1 hour

		:return:
		"""
		if self.seconds >= 60:
			self.minutes += self.seconds // 60
			self.seconds %= 60

		if self.minutes >= 60:
			self.hours += self.minutes // 60
			self.minutes %= 60

		if self.hours >= 24:
			self.days += self.hours // 24
			self.hours %= 24

		if self.days >= 7:
			self.weeks += self.days // 7
			self.days %= 7

	def add(self, s: Union[int, float], inplace: bool = False):
		"""
		Adds the given seconds

		:param s:
		:param inplace:
		:return:
		"""
		x = Time(seconds=s)
		t = self + x
		t.round = self.round
		t.simplify()
		if not inplace:
			return t
		self.__dict__.update(t.__dict__)

	def sub(self, s: Union[int, float], inplace: bool = False):
		"""
		Subtracts the given seconds

		:param s:
		:param inplace:
		:return:
		"""
		x = Time(seconds=s)
		t = self - x
		t.round = self.round
		t.simplify()
		if not inplace:
			return t
		self.__dict__.update(t.__dict__)


def length(*args, **kwargs) -> int:
	"""
	Computes the total string length for the args and kwargs passed

	:param args:
	:param kwargs:
	:return:
	"""
	return sum(len(x) for x in list(args) + list(kwargs.values()))
