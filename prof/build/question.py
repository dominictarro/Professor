"""

Contains classes and functions to construct question types

"""
# Foreign dependencies
from typing import Union, Optional, Callable
from string import ascii_lowercase
from fuzzywuzzy.fuzz import ratio
from discord.ext import commands
import discord
import random
import re

# Local dependencies
from prof.utils import numeric, system, event


class QuestionBase(object):
	_bool_map = {"true": True, "false": False}
	_attrs = ["type", "text", "answer", "image", "bot", "guild", "id", "version"]
	__help = "**Formatted** help text for __question type__."

	def __init__(self, type: str, *args, **kwargs):
		"""
		Abstract class for question types to inherit from

		:param type:    Question's structure type
		:param version: Number of versions
		:param text:    Question's text
		:param answer:  Question's answer
		:param image:   Image to include
		:param bot:     Discord bot's instance
		:param guild:   Discord guild
		:param id:      Question's integer id
		--------------------------------------
		Subclass parameters
		:param options:     Possible answers
		:param exact:       Whether answer must be correct character for character
		:param shuffle:     Shuffle options
		:param all:         All answers must be selected
		:param partial:     Partial credit for response

		"""
		self.type: str = type
		self.version: int = 1
		self.text: Optional[str] = None
		self.image: Optional[bytes] = None
		self.answer: Optional[Union[str, int, float]] = None
		self.guild: Optional[discord.Guild] = None
		self.id: int = 0

		# Drop unsupported keyword attributes
		exclude = set(kwargs.keys()) - set(self._attrs)
		for key in exclude:
			kwargs.pop(key)

		self.__dict__.update(kwargs)
		self.build(*args, **kwargs)

	@classmethod
	def help(cls) -> str:
		return cls.__help

	@property
	def dict(self) -> dict:
		return self._base_dict()

	@property
	def qtype(self) -> str:
		"""
		Returns a presentable question type

		:return:
		"""
		return re.sub('-', ' ', string=self.type).title()

	def embed(self, i: int) -> discord.Embed:
		"""
		Embed function to augment in subclasses

		:param i:
		:return:
		"""
		return self.base_embed(i=i)

	def base_embed(self, i: int) -> discord.Embed:
		"""
		Generates and returns the question's embed with an index

		:return:
		"""
		embed = discord.Embed(
			title=f"Question {i}",
			description=self.text,
			colour=discord.Colour.dark_theme()
		)
		embed.set_thumbnail(url=self.guild.icon_url)
		embed.set_footer(text=self.qtype)
		return embed

	@property
	def editor_embed(self):
		return self._base_editor_embed()

	def _base_dict(self):
		"""
		Returns the basic question attributes in dictionary form

		:return:
		"""
		return dict(
			id=self.id,
			type=self.type,
			version=self.version,
			text=self.text,
			image=self.image,
			answer=self.answer
		)

	def _base_editor_embed(self) -> discord.Embed:
		"""
		Generates and returns the question's attributes as an embed

		:return:
		"""
		embed = discord.Embed(
			title=f"{self.qtype}",
			description=self.text,
			colour=discord.Colour.purple()
		)
		embed.set_thumbnail(url=self.guild.icon_url)
		embed.add_field(name="Question Description", value=self.text, inline=False)
		embed.add_field(
			name="Answer",
			value=self.answer if len(self.answer) < (Lmax := system.EmbedLimits.Field.Value) else self.answer[:Lmax-3] + '...',
			inline=False
		)
		return embed

	def __eq__(self, other: Union[str, int, float]):
		return self.check(other)

	def build(self, *args, **kwargs):
		"""
		Placeholder method for augmenting the parameters after initialization

		:param args:
		:param kwargs:
		:return:
		"""
		pass

	def convert_response(self, text: str) -> Union[str, int, float]:
		"""
		Converts a user's response to the format desired by the subclass.
		Particularly for multiple choice/answer

		:param text: The user's response

		:return:
		"""
		return text

	def check(self, other: Union[str, int, float]) -> bool:
		"""
		Method for checking equivalency of answer and other.

		:param other: The user's response
		:return:
		"""
		return other == self.answer

	def edit_boolean(self, change: str, attribute: str):
		"""
		Edits the value of a boolean attribute

		:param change:      New value
		:param attribute:   Variable to change
		:return:
		"""
		_map = {"true": True, "false": False}
		if (change := change.lower()) in _map:
			self.__dict__[attribute] = _map[change]
			return True
		return False

	@event.on_change_embed
	@event.string_field_size_enforce(field_type="description", arg_i=0, arg_key="change")
	def edit_text(self, change: str) -> bool:
		"""
		Edits the text attribute of the question

		:return:
		"""
		self.text = change
		return True

	@event.on_change_embed
	def edit_answer(self, change: str) -> bool:
		"""
		Edits the answer attribute of the question

		:param change:
		:return:
		"""
		self.answer = change
		return True

	@event.on_change_embed
	def edit_type(self, change: str):
		"""
		Modifies the question type

		:return:
		"""
		if change in Question.types():
			params = self.dict
			params.pop("type")
			new = Question(params, type=change)
			self.__dict__.update(new.__dict__)
			self.__class__ = new.__class__
			return True
		return False


class FreeResponse(QuestionBase):
	__help = """To answer a free response question, enter, in precise words, your response.
	Be careful! Not all quiz builders are lenient on punctuation, capitalization, and spelling.
	
	e.g. What is the capital of Norway?
	`Oslo`
	or, if the quiz builder allows it,
	`oslo`
	"""

	def __init__(self, *args, **kwargs):
		"""
		...
		:param exact:   If the response must mirror the answer word for word (use Levenshtein otherwise)

		:param args:
		:param kwargs:
		"""
		self.exact = False
		self._min_ratio = 70
		self._attrs.extend(["exact"])
		super(FreeResponse, self).__init__("free-response", *args, **kwargs)

	@property
	def dict(self):
		dct = self._base_dict()
		dct.update({"exact": self.exact})
		return dct

	@property
	def editor_embed(self) -> discord.Embed:
		embed = self._base_editor_embed()
		embed.insert_field_at(index=0, name="Exact", value=str(self.exact))
		return embed

	@property
	def precision(self) -> int:
		if not self.exact:
			# If not exact, the Levenshtein ratio minimum is set as a percentage of the answer size
			# or, if short, default is at 70
			L = len(self.answer)
			precision_low_bound = int(round(100 - 100 / (L ** 0.5)))
			return max(self._min_ratio, precision_low_bound)
		return 100

	def build(self, *args, **kwargs):
		"""
		Method for augmenting the parameters after initialization

		:param args:
		:param kwargs:
		:return:
		"""
		if isinstance(self.answer, (int, float)):
			self.answer = str(self.answer)
		elif isinstance(self.answer, (list, tuple, set)):
			if self.answer:
				self.answer = random.choice(self.answer)
			else:
				self.answer = None

	def check(self, other: Union[str, int, float]) -> bool:
		"""
		Validates a string against the question's answer

		:param other:
		:return:
		"""
		return ratio(other, self.answer) >= self.precision

	@event.on_change_embed
	def edit_exact(self, change: str) -> bool:
		"""
		Edits the free-response question's 'exact' attribute

		:param change:
		:return:
		"""
		return self.edit_boolean(change=change, attribute="exact")


class Numeric(QuestionBase):
	__help = """To answer a numeric question, enter the number that answers the question (digits, not words). \
	Be careful! Some quiz builders may require rounding to a certain decimal place.

	e.g. What is 2/3 (round to the hundredths place)
	`0.67`
	You are not penalized for higher precision, we will round for you.
	`0.66667`
	"""

	def __init__(self, *args, **kwargs):
		"""
		...
		:param decimal: How many decimal places to round answers to.

		:param args:
		:param kwargs:
		"""
		self.decimal: Optional[int] = None
		self._attrs.extend(["decimal"])
		super(Numeric, self).__init__("numeric", *args, **kwargs)

	@property
	def dict(self) -> dict:
		dct = self._base_dict()
		dct.update({"decimal": self.decimal})
		return dct

	@property
	def editor_embed(self) -> discord.Embed:
		embed = self._base_editor_embed()
		embed.insert_field_at(index=0, name="Decimal", value=str(self.decimal))
		return embed

	@staticmethod
	def _numeric_string(string: str) -> Optional[Union[int, float]]:
		partial = string.split('.')
		if string.isnumeric():
			return int(string)
		elif all(x.isnumeric() for x in partial) & (0 < len(partial) < 3):
			return float(string)
		else:
			return None

	def build(self, *args, **kwargs):
		"""
		Method for augmenting the parameters after initialization

		:param args:
		:param kwargs:
		:return:
		"""
		if isinstance(self.answer, (int, float)):
			self.answer = round(self.answer, self.decimal)
		elif isinstance(self.answer, str):
			# If it is a string, check if it is a numeric string
			converted = self._numeric_string(string=self.answer)
			if converted is not None:
				self.answer = converted
		elif isinstance(self.answer, (list, tuple, set)):
			numeric_answers = []
			# Check answers for numeric answers
			for ans in self.answer:
				converted = self._numeric_string(string=ans)
				if converted is not None:
					numeric_answers.append(converted)
			# Choose one of the numeric answers or set answers equal to None
			if numeric_answers:
				self.answer = random.choice(numeric_answers)
			else:
				self.answer = None
		else:
			self.answer = None

	def check(self, other: str) -> bool:
		"""
		Validates a string against the question's answer

		:param other:
		:return:
		"""
		numer_response = self._numeric_string(other)
		return round(numer_response, self.decimal) == round(self.answer, self.decimal) if numer_response is not None else False

	@event.on_change_embed
	def edit_decimal(self, change: str) -> bool:
		"""
		Edits the value of the decimal attribute

		:param change:
		:return:
		"""
		if change.isnumeric():
			self.decimal = int(change)
			return True
		elif change.lower() == 'none':
			self.decimal = None
		return False

	@event.on_change_embed
	def edit_answer(self, change: str) -> bool:
		"""
		Edits the value of the answer attribute

		:param change:
		:return:
		"""
		converted = self._numeric_string(string=change)
		if converted is not None:
			self.answer = converted
			return True
		return False


class MultipleChoice(QuestionBase):

	__help = """To answer a multiple choice question, enter the character that is paired with the option you choose. \
	You can enter the option's text itself, but this is not advised if the option contains formatting.

	e.g. What general united Germany and founded the modern German state?
	>>>a) Otto von Bismarck
	b) Adolf Hitler
	c) Wilhelm II
	
	`c`
	"""

	def __init__(self, *args, **kwargs):
		"""
		...
		:param options: Array of options users can choose from
		:param shuffle: To scramble the order of the options

		:param args:
		:param kwargs:
		"""
		self.options: list = []
		self.shuffle: bool = False
		self._attrs.extend(["options", "shuffle"])
		super(MultipleChoice, self).__init__("multiple-choice", *args, **kwargs)
		if self.shuffle:
			random.shuffle(self.options)

	@property
	def Options(self) -> dict:
		return {ascii_lowercase[i]: opt for i, opt in enumerate(self.options)}

	@property
	def option_string(self) -> str:
		return '\n'.join(f"{a}) {opt}" for a, opt in self.Options.items())

	@property
	def dict(self):
		dct = self._base_dict()
		dct.update({"options": self.options, "shuffle": self.shuffle})
		return dct

	@property
	def editor_embed(self) -> discord.Embed:
		embed = self._base_editor_embed()
		embed.insert_field_at(index=0, name="Shuffle", value=str(self.shuffle))
		embed.insert_field_at(index=1, name="Options", value='\n'.join(f"{i+1}) {opt}" for i, opt in enumerate(self.options)))
		return embed

	def build(self, *args, **kwargs):
		"""
		Method for augmenting the parameters after initialization

		:param args:
		:param kwargs:
		:return:
		"""

		if isinstance(self.answer, (list, tuple, set)):
			# Only retain one of the answers
			# Only relevant to type transform from Multiple Response
			if self.answer:
				keep = random.choice(self.answer)
				to_remove = set(self.options).intersection(set(self.answer).difference([keep]))
				for ans in to_remove:
					self.options.remove(ans)
				self.answer = keep
			else:
				self.answer = None
		elif isinstance(self.answer, (int, float)):
			# Force to string
			self.answer = str(self.answer)

		if (self.answer not in self.options) & (self.answer is not None):
			# Ensure answer is in options
			self.options.append(self.answer)

	def embed(self, i: int) -> discord.Embed:
		"""
		Embed function to augment in subclasses

		:param i:
		:return:
		"""
		embed = self.base_embed(i=i)
		embed.insert_field_at(0, name="Options", value=self.option_string)
		return embed

	def check(self, other: str) -> bool:
		"""
		Validates a string against the question's option array or the answer itself

		:param other:
		:return:
		"""
		options = self.Options
		if other == self.answer:
			return True
		elif other in options.keys():
			return options[other] == self.answer
		return False

	def _add_option(self, change: str) -> bool:
		"""
		Base method to add an option to the option array if it meets Discord requirements.

		:param change:
		:return:
		"""
		self.options.append(change)
		if numeric.length(self.option_string) > system.EmbedLimits.Field.Value:
			self.options.pop(-1)
			return False
		return True

	@event.on_change_embed
	def add_option(self, change: str) -> bool:
		"""
		Wrapped method to add an option to the option array if it meets requisites

		:param change:
		:return:
		"""
		return self._add_option(change=change)

	@event.on_change_embed
	@event.contains(array="options")
	def edit_option(self, i: int, change: str) -> bool:
		"""
		Edits the text of an existing option.

		:param i:       Option's index
		:param change:
		:return:
		"""
		current = self.options[i]
		self.options[i] = change
		if numeric.length(self.option_string) > system.EmbedLimits.Field.Value:
			self.options[i] = current
			return False
		return True

	@event.on_change_embed
	@event.contains(array="options")
	def delete_option(self, i: int) -> bool:
		"""
		Removes an option from the option array given its index

		:param i:   Index to remove
		:return:
		"""
		self.options.pop(i)
		return True

	@event.on_change_embed
	def edit_shuffle(self, change: str):
		"""
		Changes the shuffle attribute of the quiz

		:return:
		"""
		self.edit_boolean(change=change, attribute="shuffle")


class MultipleResponse(MultipleChoice):

	__help = """To answer a multiple response question, enter the characters that are paired with the options you choose. \
	Separate them with spaces or commas.

	e.g. Which of these functions are performed by non-coding DNA?
	>>>a) Transcription
	b) Protein synthesis
	c) Transcription silencing
	d) RNA splicing
	e) Enhancer blocking

	`c e`
	or
	`c,e`
	"""

	def __init__(self, *args, **kwargs):
		self._attrs.extend(["partial"])
		super(MultipleResponse, self).__init__(*args, **kwargs)

	@property
	def editor_embed(self) -> discord.Embed:
		embed = self._base_editor_embed()
		# Drop answer field
		embed.remove_field(1)
		embed.insert_field_at(index=0, name="Shuffle", value=str(self.shuffle))
		embed.insert_field_at(index=0, name="Partial", value=str(self.partial))
		embed.add_field(name="Options", value='\n'.join(f"{i+1}) {opt}" for i, opt in enumerate(self.options)), inline=False)
		embed.insert_field_at(name="Answer", value='\n'.join(f"{i + 1}) {ans}" for i, ans in enumerate(self.answer)), inline=False)
		return embed

	def build(self, *args, **kwargs):
		"""
		Method for augmenting the parameters after initialization

		:param args:
		:param kwargs:
		:return:
		"""
		self.type = "multiple-response"

		if isinstance(self.answer, (tuple, list, set)):
			self.answer = list(self.answer)
		else:
			self.answer = [str(self.answer)] if self.answer is not None else []
		self.answer.sort()

		for ans in self.answer:
			if ans not in self.options:
				# Ensure answer is in options
				self.options.append(ans)

	def check(self, other: str) -> bool:
		"""
		Validates a string against the question's answer array or the answer itself

		:param other:
		:return:
		"""
		parts = re.split(r"[\s,]", other.lower())
		answers = self.answer.copy()
		options = self.Options
		missed = 0
		for rsp in parts:
			if rsp not in options:
				missed += 1
			elif options[rsp] not in answers:
				missed += 1
			else:
				answers.remove(options[rsp])
		return missed == 0

	@event.on_change_embed
	def add_answer(self, change: str) -> bool:
		"""
		Adds an answer to the answer array

		:param change:
		:return:
		"""
		if change not in self.options:
			if self._add_option(change=change):
				self.answer.append(change)
				return True
			return False
		self.answer.append(change)

	@event.on_change_embed
	@event.contains(array="answer")
	def edit_answer(self, i: int, change: str) -> bool:
		"""
		Edits the text of an existing option.

		:param i:       Option's index
		:param change:
		:return:
		"""
		self.answer[i] = change
		return True

	@event.on_change_embed
	@event.contains(array="answer")
	def delete_answer(self, i: int) -> bool:
		"""
		Removes an option from the option array given its index

		:param i:   Index to remove
		:return:
		"""
		self.answer.pop(i)
		return True


class Question:
	"""

	Mirror class for creating the appropriate question type.

	"""
	_map = {
		"free-response": FreeResponse,
		"numeric": Numeric,
		"multiple-choice": MultipleChoice,
		"multiple-response": MultipleResponse
	}

	def __new__(cls, doc: Optional[dict] = None, type: Optional[str] = None, **kwargs):
		"""
		Create a new question using the desired question type and its desired attributes

		:param doc:
		:param type:
		:param kwargs:
		"""
		if doc is None:
			doc = {}
		doc.update(kwargs)
		if type:
			return cls._map[type](**doc)
		elif "type" in doc:
			return cls._map[doc["type"]](**doc)
		else:
			raise AttributeError("'type' is missing from arguments")

	@classmethod
	def types(cls) -> list:
		return list(cls._map.keys())
