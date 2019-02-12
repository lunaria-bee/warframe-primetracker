import primedb as db
import wx

class TestFrame (wx.Frame):
    '''Frame for launching testing code'''
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.Button(self, -1, "TOP"), 1, wx.EXPAND, 0)
        sizer.Add(wx.Button(self, -1, "BOTTOM"), 1, wx.EXPAND, 0)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)

class PrimeApp (wx.App):

    def OnInit (self):
        frame = TestFrame(None, -1)
        frame.Show(True)
        return True


if __name__ == '__main__': PrimeApp().MainLoop()
