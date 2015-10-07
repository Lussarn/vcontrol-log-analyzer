"""
Model information
"""
__author__ = "linus.larsson@gmail.com"

import wx
import wx.richtext as rt
from PIL import Image
import time
import datetime
import re
import StringIO

import vc.globals
import vc.util
import vc.screenshot

class ModelInfoWindow(wx.Frame):
    """
    Model info Window
    """
    def __init__(self, model_id, analyzer, main_window):
        self._analyzer = analyzer
        self._model_id = model_id
        self._main_window = main_window
        self._is_info_dirty = False

        data = analyzer.extract_model_info(model_id)

        wx.Frame.__init__(self, None, title=vc.globals.PROGRAM_NAME + " " + vc.globals.VERSION + " - Model info ", size=(566, 600))

        self.SetBackgroundColour("white")
        main_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_vertical_sizer)

        top_panel = wx.Panel(self)
        top_horiz_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_panel.SetSizer(top_horiz_sizer)
        main_vertical_sizer.Add(top_panel, 0, wx.EXPAND)

        info_panel = wx.Panel(top_panel)
        gs = wx.FlexGridSizer(6, 2, 10, 20)
        info_panel.SetSizer(gs)

        info_text_static_box = wx.StaticBox(top_panel, -1, label=_("Statistics").decode("utf8"))
        info_text_static_box_sizer = wx.StaticBoxSizer(info_text_static_box, wx.VERTICAL)
        top_horiz_sizer.Add(info_text_static_box_sizer, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        
        header_font = wx.Font(family=wx.DEFAULT, pointSize=8, weight=wx.BOLD, style=wx.NORMAL)
        value_font = wx.Font(family=wx.DEFAULT, pointSize=8, weight=wx.NORMAL, style=wx.NORMAL)

        # Model name
        c1 = wx.StaticText(info_panel, label=_("Model name").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)  
        c1.SetFont(header_font)
        gs.Add(c1, 1, wx.EXPAND)
        c2 = wx.StaticText(info_panel, label=data["name"], style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c2.SetFont(value_font)
        gs.Add(c2, 1, wx.EXPAND)

        # Model type
        c3 = wx.StaticText(info_panel, label=_("Type").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c3.SetFont(header_font)
        gs.Add(c3, 1, wx.EXPAND)

        model_type = _("Helicopter").decode("utf8")
        if data["type"] == "MULTIROTOR":
            model_type = _("Multirotor").decode("utf8")
        elif data["type"] == "AIRPLANE":
            model_type = _("Airplane").decode("utf8")
        
        c4 = wx.StaticText(info_panel, label=model_type, style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)   
        c4.SetFont(value_font)
        gs.Add(c4, 1, wx.EXPAND)

        # First flight
        c5 = wx.StaticText(info_panel, label=_("First flight").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c5.SetFont(header_font)
        gs.Add(c5, 1, wx.EXPAND)

        c6 = wx.StaticText(info_panel, label=data["first"], style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)   
        c6.SetFont(value_font)
        gs.Add(c6, 1, wx.EXPAND)

        # Last flight
        c7 = wx.StaticText(info_panel, label=_("Last flight").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE) 
        c7.SetFont(header_font)
        gs.Add(c7, 1, wx.EXPAND)

        c8 = wx.StaticText(info_panel, label=data["last"], style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c8.SetFont(value_font)
        gs.Add(c8, 1, wx.EXPAND)

        # Number of flights
        c9 = wx.StaticText(info_panel, label=_("Number of flights").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)   
        c9.SetFont(header_font)
        gs.Add(c9, 1, wx.EXPAND)

        c10 = wx.StaticText(info_panel, label=str(data["cycles"]), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c10.SetFont(value_font)
        gs.Add(c10, 1, wx.EXPAND)

        # Flight time
        c11 = wx.StaticText(info_panel, label=_("Flight time").decode("utf8"), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)    
        c11.SetFont(header_font)
        gs.Add(c11, 1, wx.EXPAND)

        c12 = wx.StaticText(info_panel, label=str(data["duration"]), style=wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)  
        c12.SetFont(value_font)
        gs.Add(c12, 1, wx.EXPAND)

        info_text_static_box_sizer.Add(info_panel, 0, wx.ALL, 10)

        # Photo panel
        self._no_photo_panel = wx.Panel(top_panel, style=wx.SIMPLE_BORDER)
        self._photo_panel = wx.Panel(top_panel)
        no_photo_sizer = wx.BoxSizer(wx.VERTICAL)
        self._no_photo_panel.SetSizer(no_photo_sizer)
        top_horiz_sizer.Add(self._no_photo_panel, 1, wx.TOP  | wx.EXPAND, 18)

        photo_sizer = wx.BoxSizer(wx.VERTICAL)
        self._photo_panel.SetSizer(photo_sizer)
        top_horiz_sizer.Add(self._photo_panel, 1, wx.TOP  | wx.EXPAND, 18)
        top_horiz_sizer.AddSpacer(10)

        photo_font = wx.Font(family=wx.DEFAULT, pointSize=13, weight=wx.NORMAL, style=wx.NORMAL)
        no_photo_text = wx.StaticText(self._no_photo_panel, label=_("Drag photo here").decode("utf8"), style=0)
        no_photo_text.SetFont(photo_font)
        no_photo_text.SetForegroundColour("blue")
        no_photo_sizer.AddStretchSpacer(1)
        no_photo_sizer.Add(no_photo_text, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        no_photo_sizer.AddStretchSpacer(1)

        photo_bitmap = data["image"]
        if photo_bitmap is None:
            photo_bitmap = wx.EmptyBitmap( 1, 1 )
        else:
            # Create a PIL image from the photo to be able to create the thumbnail
            photo_image_wx = wx.ImageFromBitmap(photo_bitmap)
            photo_image_pil = Image.new("RGB", (photo_image_wx.GetWidth(), photo_image_wx.GetHeight()))
            photo_image_pil.fromstring(photo_image_wx.GetData())
            photo_image_pil.thumbnail((314, 176))
            # Create the WX Bitmap back from the PIL image 
            photo_image_wx = wx.EmptyImage(photo_image_pil.size[0],photo_image_pil.size[1])
            photo_image_wx.SetData(photo_image_pil.convert("RGB").tostring())
            photo_bitmap = wx.BitmapFromImage(photo_image_wx)

        self.model_photo_bitmap = wx.StaticBitmap(self._photo_panel, bitmap=photo_bitmap)
        photo_sizer.Add(self.model_photo_bitmap, 0, wx.CENTER)

        # Determine which panel to whow based on if there is an image or not
        if data["image"] is None:
            self._photo_panel.Hide()
            self._no_photo_panel.Show()
        else:
            self._no_photo_panel.Hide()
            self._photo_panel.Show()

        # We need two droptargets, on if we have photo, one if not
        self._photo_drop_target = PhotoDropTarget(self, self._analyzer, self._model_id)
        self._photo_panel.SetDropTarget(self._photo_drop_target)
        self._no_photo_drop_target = PhotoDropTarget(self, self._analyzer, self._model_id)
        self._no_photo_panel.SetDropTarget(self._no_photo_drop_target)

        # Screenshot
        screenshot_panel = wx.Panel(self)
        screenshot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        screenshot_panel.SetSizer(screenshot_sizer)
        main_vertical_sizer.Add(screenshot_panel, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Notes
        self._notes_text = wx.StaticText(screenshot_panel, label=_("Information").decode("utf8"), style=0)
        screenshot_sizer.Add(self._notes_text, 0, wx.ALIGN_BOTTOM)

        self.screenshot_button = wx.BitmapButton(
            screenshot_panel, 
            -1,
            wx.Bitmap(vc.util.resource_path("assets/img/screenshot16.png"), wx.BITMAP_TYPE_PNG), 
            pos=(0, 0)
        )
        screenshot_sizer.AddStretchSpacer(1)
        screenshot_sizer.Add(self.screenshot_button, 0, wx.ALIGN_RIGHT , 0)
        self.Bind(wx.EVT_BUTTON, self._on_screenshot, self.screenshot_button)

        self._textarea = rt.RichTextCtrl(self, -1)
        self._textarea.WriteText(data["info"])
        self._textarea.SetInsertionPoint(0)
        self._textarea.Bind(wx.EVT_KEY_UP, self._on_info_key, self._textarea)
        main_vertical_sizer.Add(self._textarea, 1, wx.EXPAND | wx.LEFT | wx.RIGHT| wx.BOTTOM, 10)
        self._syntax_hilight(all=True)

        self.Bind(wx.EVT_CLOSE, self._on_close)

        # Timer is used to autosave the info
        TIMER_ID = 10000 + self._model_id 
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(5000)
        wx.EVT_TIMER(self, TIMER_ID, self._on_timer)

        self.Show()

    def insert_date(self, date):
        [text, insert_pos] = self._insert_date(self._textarea.GetValue(), date)
        self._textarea.SetValue(text)
        self._textarea.SetInsertionPoint(insert_pos)
        self._textarea.SetFocus()
        self._syntax_hilight(all=True)
        self._textarea.ShowPosition(insert_pos)


    def _insert_date(self, text, date):
        """
        Insert a date at the correct place in the info
        """
        date_timestamp = self._date_to_timestamp(date)
        regexp_date = "## \\d\\d\\d\\d-\\d\\d-\\d\\d ##"
        insert_pos = len(text) -1
        for m in re.finditer(regexp_date, text):
            date_match = m.group(0)
            date_match_timestamp = self._date_to_timestamp(date_match[3:13])
            if date_match_timestamp is None:
                continue
            start = m.start()

            if date_match_timestamp > date_timestamp:
                text = text[0:start] + "## " + date + " ##\n\n" + text[start:]
                insert_pos = start + 17
                return [text, insert_pos]

            if date_match_timestamp == date_timestamp:
                insert_pos = start + 17
                return [text, insert_pos]

        text = (text.rstrip() + "\n\n## " + date + " ##").lstrip() + "\n\n"
        return [text, len(text) -1]

    def _date_to_timestamp(self, date):
        try:
            t = time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())
        except:
            t = None
        return t

    def _syntax_hilight(self, all=False):
        regexp_date = "## \\d\\d\\d\\d-\\d\\d-\\d\\d ##"
        pos = 0

        header_style = rt.RichTextAttr(wx.TextAttr((0, 0, 0)));
        header_style.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        header_style.SetLineSpacing(10)
        header_style.SetFontSize(11)
        header_style.SetFontFaceName("Courier New")

        normal_style = rt.RichTextAttr(wx.TextAttr((40, 40, 40)));
        normal_style.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        normal_style.SetLineSpacing(10)
        normal_style.SetFontSize(9)
        normal_style.SetFontFaceName("Verdana")

        date_style = rt.RichTextAttr(wx.TextAttr((0, 0, 0)));
        date_style.SetFontWeight(wx.FONTWEIGHT_BOLD)
        date_style.SetLineSpacing(10)
        date_style.SetFontSize(10)
        date_style.SetFontFaceName("Verdana")

        self._textarea.Freeze()
        cursor_pos = self._textarea.GetInsertionPoint()
        for m in re.finditer(regexp_date, self._textarea.GetValue()):
            date_match = m.group(0)
            start_match = m.start()
            if not all and abs(cursor_pos - start_match) > 1000:
                pos = start_match
                continue
            end_match = start_match + 17

            r = rt.RichTextRange(pos, start_match)
            if pos == 0:
                self._textarea.SetStyle(r, header_style)
            else:
                self._textarea.SetStyle(r, normal_style)

            r = rt.RichTextRange(start_match, end_match - 1)
            self._textarea.SetStyle(r, date_style)

            pos = end_match - 1

        r = rt.RichTextRange(pos, len(self._textarea.GetValue()))
        if pos == 0:
            self._textarea.SetStyle(r, header_style)
        else:
            self._textarea.SetStyle(r, normal_style)

        self._textarea.Thaw()
        return

    def _on_info_key(self, event):
        self._is_info_dirty = True
        self._syntax_hilight()

    def _set_photo_bitmap(self, photo_bitmap):
        self.model_photo_bitmap.SetBitmap(photo_bitmap)

    def _on_screenshot(self, event):
        # Hide some stuff we do not want in the screenshot
        self._notes_text.GetParent().GetSizer().Hide(self._notes_text)
        self.screenshot_button.GetParent().GetSizer().Hide(self.screenshot_button)
        self.screenshot_button.GetParent().GetSizer().Layout()

        vc.screenshot.grab(self, False)

        # Show some stuff we previously hide
        self._notes_text.GetParent().GetSizer().Show(self._notes_text)
        self.screenshot_button.GetParent().GetSizer().Show(self.screenshot_button)
        self.screenshot_button.GetParent().GetSizer().Layout()      

    def _on_close(self, event):
        if self._is_info_dirty == True:
            self._analyzer.set_model_info(self._model_id, self._textarea.GetValue())
            self._main_window.update_gear(
                type="model",
                id=self._model_id,
                data={"info": self._textarea.GetValue()}
            )
            
        self._main_window.populate_grid(reload=False)
        del self._main_window.model_info_windows[self._model_id]


        self.Destroy()

    def _on_timer(self, event):
        if self._is_info_dirty == True:
            self._analyzer.set_model_info(self._model_id, self._textarea.GetValue())
            self._main_window.update_gear(
                type="model",
                id=self._model_id,
                data={"info": self._textarea.GetValue()}
            )
        self._is_info_dirty = False




class PhotoDropTarget(wx.FileDropTarget):
    """
    Photo drop target

    Drag image files onto the drop
    """
    def __init__(self, window, analyzer, model_id):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self._analyzer = analyzer
        self._model_id = model_id

    def OnDropFiles(self, x, y, filenames):
        """
        Droptarget function
        """
        filename = filenames[0]
        try:
            photo_original_image_pil = Image.open(filename)
            # Copy the image since we need 3 of them (Original, thumb and info size)
            # The info thumb is never saved, but updated in the info window
            photo_thumb_image_pil = photo_original_image_pil.copy()
            photo_info_image_pil = photo_original_image_pil.copy()

            # Create thumbnail
            photo_thumb_image_pil.thumbnail((140, 79))
            photo_thumb_string_io = StringIO.StringIO()
            photo_thumb_image_pil.save(photo_thumb_string_io, "PNG")
            photo_thumb_image_pil = photo_thumb_string_io.getvalue()

            # Create original
            photo_original_image_pil.thumbnail((1152, 648))
            result = StringIO.StringIO()
            photo_original_image_pil.save(result, "PNG")
            photo_original_image_pil = result.getvalue()

            # Save images to model in DB
            self._analyzer.set_model_image(self._model_id, photo_thumb_image_pil, photo_original_image_pil)

            # Update model info window with new image
            photo_info_image_pil.thumbnail((314, 176))
            photo_image_wx = wx.EmptyImage(photo_info_image_pil.size[0],photo_info_image_pil.size[1])
            photo_image_wx.SetData(photo_info_image_pil.convert("RGB").tostring())
            photo_bitmap = wx.BitmapFromImage(photo_image_wx)
            self.window._set_photo_bitmap(photo_bitmap) 

            # Reflow UI after updating image
            self.window._no_photo_panel.Hide()
            self.window._photo_panel.Show()
            self.window.GetSizer().Layout()
       
        except:
            pass

        self.window._main_window.populate_gear()
        self.window._main_window.populate_grid()
