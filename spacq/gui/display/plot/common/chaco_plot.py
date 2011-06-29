from chaco.api import Plot
from chaco.tools.api import BetterSelectingZoom, PanTool

"""
Chaco wrapper.
"""


class ChacoPlot(Plot):
	"""
	A 2D Chaco plot wrapped with useful common functionality.
	"""

	@staticmethod
	def sci_formatter(value):
		"""
		Convert a value to a scientific notation string as applicable.
		"""

		# Subtly different from g or n presentation types.
		if value != 0 and (abs(value) < 1e-3 or abs(value) > 1e3):
			parts = '{0:e}'.format(value).split('e')
			result = parts[0].rstrip('0').rstrip('.') + 'e' + parts[1]
		else:
			result = '{0:f}'.format(value).rstrip('0').rstrip('.')

		return result

	def configure(self):
		"""
		Configure padding, tools, etc.
		"""

		# Padding.
		self.padding = 20
		self.padding_left = 120
		self.padding_bottom = 55

		# Axes.
		self.index_axis.tick_label_formatter = self.sci_formatter
		self.value_axis.tick_label_formatter = self.sci_formatter

		# Tools.
		self.tools.append(PanTool(self))

		zoom = BetterSelectingZoom(self)
		self.tools.append(zoom)
		self.overlays.append(zoom)

	@property
	def x_label(self):
		"""
		The x axis label.
		"""

		return self.index_axis.title

	@x_label.setter
	def x_label(self, value):
		self.index_axis.title = value

	@property
	def y_label(self):
		"""
		The y axis label.
		"""

		return self.value_axis.title

	@y_label.setter
	def y_label(self, value):
		self.value_axis.title = value
