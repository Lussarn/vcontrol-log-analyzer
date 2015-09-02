import wx

class VBLogWindow(wx.Frame):
	def __init__(self, logId, analyzer):
		data = analyzer.extract_log(logId)
		wx.Frame.__init__(self, None, title='VBar Control flight analyzer v2.6.0 - Log Id ' + logId, size=(1200, 700))

		textarea = wx.TextCtrl(self, -1,
                                style=wx.TE_MULTILINE|wx.BORDER_SUNKEN|wx.TE_READONLY|
                                wx.TE_RICH2)

		for row in data:
			line = row['date'] + ' (' + str(row['severity']) + ') ' + row['message'] + "\n"

			if row['severity'] == 4:
				textarea.SetDefaultStyle(wx.TextAttr(wx.RED))
			else:
				textarea.SetDefaultStyle(wx.TextAttr(wx.BLACK))
			textarea.WriteText(line)
		textarea.SetInsertionPoint(0)

		self.Show()