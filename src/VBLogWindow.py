"""
VBar log window
"""
__author__ = "linus.larsson@gmail.com"

import wx

import vc.globals

class VBLogWindow(wx.Frame):
    """
    VBar Log window class
    """
    def __init__(self, log_id, analyzer):
        data = analyzer.extract_vbar_log(log_id)
        wx.Frame.__init__(self, None, title=vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Log Id " + log_id, size=(500, 700))

        textarea = wx.TextCtrl(
            self, 
            -1,
           style=wx.TE_MULTILINE | wx.BORDER_SUNKEN | wx.TE_READONLY | wx.TE_RICH2
        )

        for row in data:
            line = row["date"] + " (" + str(row["severity"]) + ") " + row["message"] + "\n"
            if row['severity'] == 4:
                textarea.SetDefaultStyle(wx.TextAttr(wx.RED))
            else:
               textarea.SetDefaultStyle(wx.TextAttr(wx.BLACK))

            textarea.WriteText(line)

        textarea.SetInsertionPoint(0)

        self.Show()
