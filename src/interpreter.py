"""

Interpreter for bot commands, quiz/question edits, and response editing

"""
from typing import Union, List, Tuple, Optional
from discord.ext import commands
import discord
import re


class CommandInterpreter:
	# Parses the flags in a bot command
	__free_rgx = re.compile(r"(?P<flag>[a-zA-z]+?)(\s|$)", flags=re.DOTALL)
	__keyword_rgx = re.compile(r'(?P<flag>[a-zA-z]+?)=(?P<value>(".+?")|([\S]+?))(\s|$)', flags=re.DOTALL)
	default_scope = [
		"sync", "async", "period", "limit",
		"shuffle", "size", "id", "public",
		"new", "global", "plot", "history",
		"quiz"
	]
	to_int = ["id", "size"]

	"""

	:param __free_rgx:      Regex for free flags
	:param __keyword_rgx:   Regex for keyword flags
	:param default_scope:   Accepted flags
	:param to_int:          Flags that should be converted to integers
	"""

	@classmethod
	def read(cls, string: str, scope: Optional[tuple] = None):
		"""
		Parses keyword and free flags from a string

		<prefix><operator> <parameter> <flags>

		free flags      -<flag>
		keyword flags:  -<flag>=<value>

		:param string:  String to extract flags from
		:param scope:   Flags to search for
		:return:
		"""
		if scope is None:
			scope = cls.default_scope

		flags = {}
		# Grab keyword flags
		keyword = cls.__keyword_rgx.finditer(string=string)
		if keyword:
			for match in keyword:
				# Verify in scope
				if match.group("flag") in scope:
					flags[match.group("flag")] = match.group("value").strip('"')

		# Grab free flags
		free = cls.__free_rgx.finditer(string=string)
		if free:
			for match in free:
				# Verify in scope
				if match.group("flag") in scope:
					flags[match.group("flag")] = True


		# Conversion
		for key in set(cls.to_int).intersection(flags.keys()):
			flags[key] = int(flags[key]) if flags[key].isnumeric() else flags[key]

		return flags

	@classmethod
	def parser(cls, scope: Optional[tuple] = None):
		"""
		Parsing wrapper for retrieving specific flags

		:param scope:
		:return:
		"""
		def metawrap(f):
			def wrap(inst, obj, *args, **kwargs):
				flags = {}
				# Get flags
				if isinstance(obj, discord.Message):
					flags = CommandInterpreter.read(string=obj.content, scope=scope)
				elif isinstance(obj, commands.Context):
					flags = CommandInterpreter.read(string=obj.message.content, scope=scope)
				return f(inst, *args, flags=flags, **kwargs)
			return wrap
		return metawrap


class QuizInterpreter:

	operator_rgx = re.compile(r"^\$(?P<operator>[a-zA-z]+?)(\s|$)")
	param_rgx = re.compile(r"(?P<param>[a-zA-z]+?)=(?P<value>(\".+?\")|([\S]+?))(\s|$)", flags=re.DOTALL)

	@classmethod
	def read(cls, string: str):
		"""
		Extracts a quiz operator and arguments from a string

		:param string:
		:return:
		"""
		# Arrays of the operator, parameter, value
		edits = []
		op = cls.operator_rgx.match(string)
		op = op
		par = cls.param_rgx.finditer(string)

		if op and par:
			op = op.group("operator")
			for arg in par:
				param = arg.group("param")
				value = arg.group("value")

				edits.append((op, param, value))

		return edits


class QuestionInterpreter:

	rgx = re.compile(r"^(?P<index>[0-9]+?)\.(?P<subindex>[0-9]*?)\s\$(?P<operator>[a-zA-z]+?)\s(?P<param>[a-zA-Z]+?)\s(?P<value>.*?)$", flags=re.DOTALL)
	default_operator_scope = [
		"add", "delete", "edit", "move"
	]

	@classmethod
	def read(cls, string):

		match = cls.rgx.match(string)

		if match:
			output = match.groupdict()

			output["index"] = int(output["index"])
			output["subindex"] = int(output["subindex"]) if output["subindex"].isnumeric() else None

			return output


if __name__ == "__main__":

	command_cases = [
		"dr.open quiz=\"Big Brain Trivia\" sync period=0:30.5:0",
		"dr.open quiz=\"Big Brain Trivia\"",
		"dr.edit quiz=Film period=0.33333333:30:0 sync size=10",
		"dr.open quiz=Film-School sync",
		"dr.metrics plot public"
	]

	for case in command_cases:
		print(case)
		print(CommandInterpreter.read(case))#, scope=("sync", "period")))
		print('-')

	print('-'*10)

	quiz_cases = [
		"$edit name=Burgerville size=10",
		"$delete question=1",
		"$add question=free-response",
		'$edit name="Big Brain Trivia"',
		'$edit name="Big Brain Trivia" size=10'
	]

	for case in quiz_cases:
		print(case)
		print(QuizInterpreter.read(case))
		print('-')

	print('-'*10)

	question_cases = [
		"1. $edit text Burgerville",
		"2.1 $move insert 3",
		"3. $add option George Lopez",
		"2.2 $edit answer First Battle of Bunker Hill",
		"1. $edit type free-response"
	]
	for case in question_cases:
		print(case)
		print(QuestionInterpreter.read(case))
		print('-')
