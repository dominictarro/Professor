"""

Contains utility functions for augmenting events and callbacks

"""
from typing import Callable, Optional, Union
import discord
import random
import json

from professor.utils.numeric import length
from professor.utils.system import EmbedLimits


def on_change_embed(f: Callable) -> Callable:
	"""
	Wrap change commands to returns the embed function to be updated with an index and posted.

	:param f:
	:return:
	"""
	def wrap(inst, *args, **kwargs) -> Optional[object]:
		if f(inst, *args, **kwargs):
			# TODO
			return inst.editor_embed
		return None
	return wrap


def string_field_size_enforce(field_type: str = "description", arg_i: Optional[int] = None, arg_key: Optional[str] = None) -> Callable:
	"""
	Wrap change commands to enforce Discord embed length requirements based on where change is occuring in embed

	:param field_type:      Can take on title, description, field-name, field-value.
	:param arg_i:           Where item whose size must be modified is placed in the arguments
	:param arg_key:         Key for keyword argument
	:return:
	"""

	if field_type == "description":
		condition = EmbedLimits.Description
	elif field_type == "title":
		condition = EmbedLimits.Title
	elif field_type == "field-name":
		condition = EmbedLimits.Field.Name
	elif field_type == "field-value":
		condition = EmbedLimits.Field.Value
	else:
		raise Exception(f"{field_type} not supported by size_enforce")

	unit_logical: Callable = lambda x: len(x) <= condition

	if (arg_i is None) & (arg_key is None):
		raise Exception(f"{arg_i} and {arg_key} are not valid indexes/keys")

	get_kwarg: Callable = lambda args, kwargs: kwargs[arg_key]
	get_arg: Callable = lambda args, kwargs: args[arg_i]

	def meta_wrap(f: Callable):
		def wrap(inst, *args, **kwargs):
			"""
			Validates that an array of arguments meets length limitations for Discord Embeds

			@size_enforce(field_type='field-name', arg_i='text')
			def edit_option()

			:param inst:    Object instance
			:param args:    Method arguments
			:param kwargs:  Method keyword arguments
			:return:
			"""
			# Prioritize keyword
			if arg_key in kwargs:
				if not unit_logical(x=get_kwarg(args, kwargs)):
					return False
			if not unit_logical(x=get_arg(args, kwargs)):
				return False

			return f(inst, *args, **kwargs)
		return wrap
	return meta_wrap


def contains(array: str = ""):
	"""
	Checks if the given index/indices is/are present in the option or answer arrays

	:param array: name of the array ('option' or 'answer')
	:return:
	"""
	def metawrap(f: Callable):
		"""

		:param f: Function affecting an question that indexes
		:return:
		"""
		def wrap(inst, *args, **kwargs):
			"""
			Checks if all numeric values are inside of that array's index range

			:param inst:
			:param args:
			:param kwargs:
			:return:
			"""
			length = len(inst.__dict__[array])
			# assumes all integers are index arguments
			if all([-length <= i < length for i in list(args) + list(kwargs) if isinstance(i, int)]):
				return f(inst, *args, **kwargs)
			return False
		return wrap
	return metawrap

