import wx


class Example(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Example, self).__init__(*args, **kwargs)
        self.InitUI()
        self.Centre()

    def OnCloseWindow(self, e):
        dial = wx.MessageDialog(None, 'Are you sure to quit?', 'Question',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        ret = dial.ShowModal()
        if ret == wx.ID_YES:
            self.Destroy()
        else:
            e.Veto()

    def InitUI(self):
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        panel = wx.Panel(self)

        sizer = wx.GridBagSizer(5, 5)

        text1 = wx.StaticText(panel, label="Java Class")
        sizer.Add(text1,
                  pos=(0, 0),
                  flag=wx.TOP | wx.LEFT | wx.BOTTOM,
                  border=15)

        ## icon = wx.StaticBitmap(panel, bitmap=wx.Bitmap('exec.png'))
        ##sizer.Add(icon, pos=(0, 4), flag=wx.TOP | wx.RIGHT | wx.ALIGN_RIGHT, border=5)

        line = wx.StaticLine(panel)
        sizer.Add(line,
                  pos=(1, 0),
                  span=(1, 5),
                  flag=wx.EXPAND | wx.BOTTOM,
                  border=10)

        text2 = wx.StaticText(panel, label="Name")
        sizer.Add(text2, pos=(2, 0), flag=wx.LEFT, border=10)

        tc1 = wx.TextCtrl(panel)
        sizer.Add(tc1, pos=(2, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND)

        text3 = wx.StaticText(panel, label="Package")
        sizer.Add(text3, pos=(3, 0), flag=wx.LEFT | wx.TOP, border=10)

        tc2 = wx.TextCtrl(panel)
        sizer.Add(tc2,
                  pos=(3, 1),
                  span=(1, 3),
                  flag=wx.TOP | wx.EXPAND,
                  border=5)

        button1 = wx.Button(panel, label="Browse...")
        sizer.Add(button1, pos=(3, 4), flag=wx.TOP | wx.RIGHT, border=5)

        text4 = wx.StaticText(panel, label="Extends")
        sizer.Add(text4, pos=(4, 0), flag=wx.TOP | wx.LEFT, border=10)

        combo = wx.ComboBox(panel)
        sizer.Add(combo,
                  pos=(4, 1),
                  span=(1, 3),
                  flag=wx.TOP | wx.EXPAND,
                  border=5)

        button2 = wx.Button(panel, label="Browse...")
        sizer.Add(button2, pos=(4, 4), flag=wx.TOP | wx.RIGHT, border=5)

        sb = wx.StaticBox(panel, label="Optional Attributes")

        boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        boxsizer.Add(wx.CheckBox(panel, label="Public"),
                     flag=wx.LEFT | wx.TOP,
                     border=5)
        boxsizer.Add(wx.CheckBox(panel, label="Generate Default Constructor"),
                     flag=wx.LEFT,
                     border=5)
        boxsizer.Add(wx.CheckBox(panel, label="Generate Main Method"),
                     flag=wx.LEFT | wx.BOTTOM,
                     border=5)
        sizer.Add(boxsizer,
                  pos=(5, 0),
                  span=(1, 5),
                  flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                  border=10)

        button3 = wx.Button(panel, label='Help')
        sizer.Add(button3, pos=(7, 0), flag=wx.LEFT, border=10)

        button4 = wx.Button(panel, label="Ok")
        sizer.Add(button4, pos=(7, 3))

        button5 = wx.Button(panel, label="Cancel")
        sizer.Add(button5,
                  pos=(7, 4),
                  span=(1, 1),
                  flag=wx.BOTTOM | wx.RIGHT,
                  border=10)

        sizer.AddGrowableCol(2)

        panel.SetSizer(sizer)
        sizer.Fit(self)


def main():

    app = wx.App()
    frame = Example(None)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
