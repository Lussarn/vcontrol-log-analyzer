"""
Grab screenshot module
"""
__author__ = "linus.larsson@gmail.com"

import wx
from PIL import Image

import vc.globals
import vc.variable

class _ScaleDialog(wx.Dialog):
    """
    Opens a dialog for the scale of the image (image size)
    """
    def __init__(self):
        wx.Dialog.__init__(self, None) 
        self.scale = -1
        self.SetSize((300, 400))
        self.SetTitle(vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - " + _("Screenshot").decode("utf8"))

        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_panel.SetSizer(main_sizer)

        title = wx.StaticText(main_panel, label=_("Screenshot").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)
        title.SetFont(wx.Font(family=wx.DEFAULT, pointSize=8, weight=wx.BOLD, style=wx.NORMAL))
        main_sizer.AddSpacer(10) 
        main_sizer.Add(title, 0, wx.EXPAND | wx.LEFT, 10)

        resolution_static_box = wx.StaticBox(main_panel, -1, label=_("Image max size").decode("utf8"))
        resolution_static_box_sizer = wx.StaticBoxSizer(resolution_static_box, wx.VERTICAL)
        main_sizer.Add(resolution_static_box_sizer, 0, wx.EXPAND | wx.ALL, 6)

        # Available resolutions
        self._scale_resolutions = [
            { "scale" : 0, "label" : _("No scaling") },
            { "scale" : 600, "label" : "600px " + _("width").decode("utf8") },
            { "scale" : 700, "label" : "700px " + _("width").decode("utf8") },
            { "scale" : 800, "label" : "800px " + _("width").decode("utf8") },
            { "scale" : 900, "label" : "900px " + _("width").decode("utf8") },
            { "scale" : 1000, "label" : "1000px " + _("width").decode("utf8") },
            { "scale" : 1200, "label" : "1200px " + _("width").decode("utf8") },
            { "scale" : 1400, "label" : "1400px " + _("width").decode("utf8") },
        ]

        # Build scale radiobuttons
        checked = int(vc.variable.get("screenshot-ui-scale", "0"))
        self._scale_radio_buttons = []
        for index, resolution in enumerate(self._scale_resolutions):
            scale_button = wx.RadioButton(main_panel, label=resolution["label"])
            resolution_static_box_sizer.Add(scale_button, 0, wx.ALL, 5)
            self._scale_radio_buttons.append(scale_button)
            if index == checked:
                scale_button.SetValue(True)


        # Action buttons
        action_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(main_panel, label=_("Save image").decode("utf8"))
        action_buttons_sizer.Add(ok_button, 0, wx.ALIGN_LEFT, 10)
        close_button = wx.Button(main_panel, label=_("Cancel").decode("utf8"))
        action_buttons_sizer.Add(close_button, 0, wx.ALIGN_LEFT | wx.LEFT, 10)

        main_sizer.AddStretchSpacer(1)
        main_sizer.Add(action_buttons_sizer, 0, wx.ALL | wx.EXPAND, 10)

        ok_button.Bind(wx.EVT_BUTTON, self._on_ok)
        close_button.Bind(wx.EVT_BUTTON, self._on_close)       

    def _on_ok(self, event):
        self.scale = 0
        for index, resolution in enumerate(self._scale_resolutions):
            scale_button = self._scale_radio_buttons[index] 
            if (scale_button.GetValue() == True):
                self.scale = resolution["scale"]
                vc.variable.set("screenshot-ui-scale", str(index))
                break
        self.Close()

    def _on_close(self, event):
        self.Close()

def grab(frame, scaling=True):
    """
    Grab a screenshot with optional scaling
    """

    # Grab a window (frame) and store it in PIL image
    original_width, original_height = frame.ClientSize
    context = wx.ClientDC(frame)
    memory = wx.MemoryDC()
    bitmap = wx.EmptyBitmap(original_width, original_height, -1 )
    memory.SelectObject(bitmap )
    memory.Blit(0, 0, original_width, original_height, context, 0, 0)
    memory.SelectObject(wx.NullBitmap)
    screenshot_image_wx = bitmap.ConvertToImage()
    screenshot_image_pil = Image.new("RGB", (screenshot_image_wx.GetWidth(), screenshot_image_wx.GetHeight()))
    screenshot_image_pil.fromstring(screenshot_image_wx.GetData())

    # Optional scaling
    if (scaling):
        scale_dialog = _ScaleDialog()
        scale_dialog.ShowModal()
        scale_dialog.Destroy()

        # Cancel on the scale dialog
        if (scale_dialog.scale == -1):
            return  
        
        # Scale image
        if (scale_dialog.scale > 0):
            scale_width = scale_dialog.scale
            scale_ratio = float(scale_width) / original_width
            scale_height = int(original_height * scale_ratio)
            scale_size = scale_width, scale_height
            screenshot_image_pil.thumbnail(scale_size, Image.ANTIALIAS)        

    save_file_dialog = wx.FileDialog(
        frame, 
        "Save PNG file", 
        "", 
        "",
        "PNG files (*.png)|*.png", 
        wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    )

    if save_file_dialog.ShowModal() == wx.ID_CANCEL:
        return

    screenshot_filename = save_file_dialog.GetPath()

    try: 
        screenshot_image_pil.save(screenshot_filename,"PNG")
    except:
        wx.MessageBox(
            _("Unable to save screenshot").decode("utf8"),
            _("Error").decode("utf8"),
            wx.OK | wx.ICON_ERROR
        )

