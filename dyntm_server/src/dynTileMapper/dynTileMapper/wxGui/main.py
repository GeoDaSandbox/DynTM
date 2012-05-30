import os.path
import wx
from control import C_DyMaps

class ddtApp(wx.App):
    def __init__(self,redirect=False,filename=None):
        wx.App.__init__(self,redirect,filename)
    def OnInit(self):
        self.frame = C_DyMaps()
        self.SetTopWindow(self.frame)
        self.frame.Show()
        print "Welcome..."
        print "  This screen will display information about what's going on behind the scenes, this is mostly useful for debugging, but also lets you know that the application is running!"
        return True

if __name__=='__main__':
    app = ddtApp(redirect=True)
    app.MainLoop()

