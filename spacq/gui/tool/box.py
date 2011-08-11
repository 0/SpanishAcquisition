import csv
from os.path import basename
import pickle
import wx


OK_BACKGROUND_COLOR = 'PALE GREEN'


def determine_wildcard(extension=None, file_type=None):
	"""
	Assemble a wildcard string of the form:
		[[file_type ](*.extension)|*.extension|]<all_files>
	"""

	all_files = 'All files|*'

	if extension is not None:
		if '|' in extension:
			raise ValueError(extension)

		if file_type is not None:
			if '|' in file_type:
				raise ValueError(file_type)

			wildcard = '{0} (*.{1})|*.{1}|{2}'.format(file_type, extension, all_files)
		else:
			wildcard = '(*.{0})|*.{0}|{1}'.format(extension, all_files)
	else:
		wildcard = all_files

	return wildcard


def load_pickled(parent, extension=None, file_type=None):
	"""
	Unpickle data from a file based on a file dialog.
	"""

	wildcard = determine_wildcard(extension, file_type)
	dlg = wx.FileDialog(parent=parent, message='Load...', wildcard=wildcard,
			style=wx.FD_OPEN)

	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()

		with open(path, 'rb') as f:
			try:
				return pickle.load(f)
			except Exception as e:
				# Wrap all problems.
				raise IOError('Could not load data.', e)

def save_pickled(parent, values, extension=None, file_type=None):
	"""
	Pickle data to a file based on a file dialog.
	"""

	wildcard = determine_wildcard(extension, file_type)
	dlg = wx.FileDialog(parent=parent, message='Save...',
			wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()

		# Automatically append extension if none given.
		if extension is not None and '.' not in path:
			path = '{0}.{1}'.format(path, extension)

		with open(path, 'wb') as f:
			try:
				pickle.dump(values, f, protocol=pickle.HIGHEST_PROTOCOL)
			except Exception as e:
				# Wrap all problems:
				raise IOError('Could not save data.', e)


def load_csv(parent, extension='csv', file_type='CSV'):
	"""
	Load data from a CSV file based on a file dialog.
	"""

	wildcard = determine_wildcard(extension, file_type)
	dlg = wx.FileDialog(parent=parent, message='Load...', wildcard=wildcard,
			style=wx.FD_OPEN)

	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()

		filename = basename(path)

		with open(path, 'rb') as f:
			try:
				result = list(csv.reader(f))
				try:
					has_header = len(result[0]) > 0
				except IndexError:
					has_header = False
				else:
					# Remove empty row.
					if not has_header:
						result = result[1:]

				return (has_header, result, filename)
			except Exception as e:
				# Wrap all problems.
				raise IOError('Could not load data.', e)

def save_csv(parent, values, headers=None, extension='csv', file_type='CSV'):
	"""
	Save data to a CSV file based on a file dialog.
	"""

	wildcard = determine_wildcard(extension, file_type)
	dlg = wx.FileDialog(parent=parent, message='Save...',
			wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()

		# Automatically append extension if none given.
		if extension is not None and '.' not in path:
			path = '{0}.{1}'.format(path, extension)

		with open(path, 'wb') as f:
			try:
				w = csv.writer(f)

				if headers is not None:
					w.writerow(headers)
				else:
					w.writerow([])

				w.writerows(values)
			except Exception as e:
				# Wrap all problems:
				raise IOError('Could not save data.', e)


class Dialog(wx.Dialog):
	"""
	Auto-destroying dialog.
	"""

	def __init__(self, parent, auto_destroy=True, *args, **kwargs):
		wx.Dialog.__init__(self, parent, *args, **kwargs)

		self.auto_destroy = auto_destroy

		self.Bind(wx.EVT_SHOW, self.OnShow)

	def OnShow(self, evt):
		"""
		Destroy the dialog when it disappears.
		"""

		if self.auto_destroy and not evt.Show:
			if not self.IsBeingDeleted():
				self.Destroy()


class MessageDialog(Dialog):
	"""
	A simple error message dialog.
	"""

	def __init__(self, parent, message, title='', unclosable=False, monospace=False,
			*args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER
		if unclosable:
			kwargs['style'] &= ~wx.CLOSE_BOX

		Dialog.__init__(self, parent=parent, title=title, *args, **kwargs)

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Message.
		message_text = wx.StaticText(self, label=message)
		if monospace:
			font = message_text.Font
			message_text.Font = wx.Font(font.PointSize, wx.MODERN, font.Style, font.Weight)
		message_text.SetMinSize((450, 100))
		dialog_box.Add(message_text, proportion=1, flag=wx.EXPAND|wx.ALL, border=20)

		## OK button.
		if not unclosable:
			ok_button = wx.Button(self, wx.ID_OK)
			dialog_box.Add(ok_button, flag=wx.EXPAND)

		self.SetSizerAndFit(dialog_box)


class YesNoQuestionDialog(Dialog):
	"""
	A yes/no question dialog.
	"""

	def __init__(self, parent, prompt, yes_callback=None, no_callback=None, title='',
			*args, **kwargs):
		Dialog.__init__(self, parent=parent, title=title,
				style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
				*args, **kwargs)

		self.yes_callback = yes_callback
		self.no_callback = no_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Prompt.
		prompt_text = wx.StaticText(self, label=prompt)
		dialog_box.Add(prompt_text, proportion=1, flag=wx.EXPAND|wx.ALL, border=20)

		## Buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		yes_button = wx.Button(self, wx.ID_YES)
		self.Bind(wx.EVT_BUTTON, self.OnYes, yes_button)
		button_box.Add(yes_button)

		no_button = wx.Button(self, wx.ID_NO)
		self.Bind(wx.EVT_BUTTON, self.OnNo, no_button)
		button_box.Add(no_button)

		self.SetSizerAndFit(dialog_box)

		self.Bind(wx.EVT_CLOSE, self.OnNo)

	def OnYes(self, evt=None):
		if self.yes_callback is not None:
			self.yes_callback()

		self.Destroy()

	def OnNo(self, evt=None):
		if self.no_callback is not None:
			self.no_callback()

		self.Destroy()
