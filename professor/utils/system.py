"""

Shared variables used throughout the system

"""


class EmbedLimits(object):
	Total = 6000
	Title = 256
	Description = 2048
	Fields = 25

	class Field(object):
		Name = 256
		Value = 1024

	class Footer(object):
		Text = 2048

	class Author(object):
		Name = 256
