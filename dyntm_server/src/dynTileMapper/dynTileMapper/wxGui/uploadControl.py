import wx
from uploadModel import M_UploadTiles
from rc import DyMaps_xrc
import inspect
import types
from StringIO import StringIO
import yaml
import os.path

from wxpysal.util.progressDialog import ProgressDialog



class evt:
    """This class redirects traditional event handlers to a dispatcher"""
    def __init__(self,dispatcherMethod,name):
        self.name = name
        self.dispatcherMethod = dispatcherMethod
    def __call__(self,evt):
        """pass the evt and the name of the evt to the dispatcher"""
        self.dispatcherMethod(self.name,evt)
def remapEvtsToDispatcher(instance,dispatcherMethod):
    """ The new version of XRCED takes care of evt bindings for us,
        it also adds an evt handler for each binding,
        This function remaps those events to a dispatcher
    """
    ## identify binds and remap to dispatcher
    for name in dir(instance):
        # scan the parent class for event bindings
        if name[:2]=='On' and '_' in name:
            obj = getattr(instance,name) #grab the object from the instance
            #make sure it is an instancemethod and has the right argSpec
            if type(obj) is types.MethodType and inspect.getargspec(obj)[0] == ['self', 'evt']:
                #print "remapping instance.%s(evt) to instance.dispatch('%s',evt)"%(name,name)
                setattr(instance,name,evt(dispatcherMethod,name))

class C_UploadTiles(DyMaps_xrc.xrcUploadTiles):
    """Implements the DyMaps Frame"""
    def __init__(self,parent=None,configFile=None):
        remapEvtsToDispatcher(self,self.evtDispatch)
        DyMaps_xrc.xrcUploadTiles.__init__(self,parent)

        self.model = M_UploadTiles()
        self.model.addListener(self.populate)

        ### Dispatch should contian both model tags (model.TAGS), and widgetNames.
        self.dispatch = d = {}
        d['ServerTextCtrl'] = self.__server
        d['server'] = self.__server
        d['UserTextCtrl'] = self.__user
        d['user'] = self.__user
        d['PasswdTextCtrl'] = self.__passwd
        d['passwd'] = self.__passwd
        d['TESTCONN'] = self.verify
        d['UPLOAD'] = self.run
        d['DATA'] = self.__dataFile
        d['DATAOPEN'] = self.__dataFile
        d['mapConfig'] = self.__dataFile
        d['checkTiles'] = self.__checkTiles
        d['checkMap'] = self.__checkMap
        d['checkIDS'] = self.__checkIDS
        d['checkOverview'] = self.__checkOverview
        d['CloseButton'] = self.close

        if configFile:
            self.model.mapConfig = configFile
        self.model.checkMap = True
        self.model.checkIDS = True
        self.model.checkTiles = True
        self.model.checkOverview = True

    def close(self,evtName=None,evt=None):
        self.Close()
    def reset(self):
        self.model.reset()
    def evtDispatch(self,evtName,evt):
        evtName,widgetName = evtName.split('_',1)
        if widgetName in self.dispatch:
            self.dispatch[widgetName](evtName,evt)
        else:
            print "not implemneted:",evtName,widgetName
        #print evtName,widgetName
    def populate(self,tag=False):
        if tag:
            if tag in self.dispatch:
                self.dispatch[tag](value=self.model.getByTag(tag))
            else:
                print "Warning: %s, has not been implemented"%tag
        else:
            for key,value in self.model:
                if key in self.dispatch:
                    self.dispatch[key](value=value)
                else:
                    print "Warning: %s, has not been implemented"%key
        self.able()
    def verify(self,evtName=None,evt=None):
        try:
            if self.model.verify():
                success = wx.MessageDialog(self,"The Connection is Ready!","Success!",style=wx.OK|wx.CENTRE|wx.ICON_INFORMATION)
                success.ShowModal()
            else:
                raise ValueError,'Authenticaion Failed'
        except:
                fail = wx.MessageDialog(self,"The Server Name, Usename or Password is invalid!","Failed!",style=wx.OK|wx.CENTRE|wx.ICON_INFORMATION)
                fail.ShowModal()
    def run(self,evtName=None,evt=None):
        try:
            self.model.verify()
            self.model.run()
        except: raise
    def able(self):
        pass
    def __server(self,evtName=None,evt=None,value=None):
        if evt is not None:
            self.model.server = self.ServerTextCtrl.GetValue()
        elif value is not None:
            self.ServerTextCtrl.SetValue(value)
    def __user(self,evtName=None,evt=None,value=None):
        if evt is not None:
            self.model.user = self.UserTextCtrl.GetValue()
        elif value is not None:
            self.UserTextCtrl.SetValue(value)
    def __passwd(self,evtName=None,evt=None,value=None):
        if evt is not None:
            self.model.passwd = self.PasswdTextCtrl.GetValue()
        elif value is not None:
            self.PasswdTextCtrl.SetValue(value)
    def __checkMap(self,evtName=None,evt=None,value=None):
        if evt:
            self.model.checkMap = evt.IsChecked()
        elif value is not None:
            if self.checkMap.IsChecked() != value:
                self.checkMap.SetValue(value)
            if value:
                self.model.checkOverview = True
                self.model.checkIDS = True
    def __checkIDS(self,evtName=None,evt=None,value=None):
        if evt:
            self.model.checkIDS = evt.IsChecked()
        elif value is not None:
            if self.checkIDS.IsChecked() != value:
                self.checkIDS.SetValue(value)
            if not value:
                self.model.checkMap = False
    def __checkOverview(self,evtName=None,evt=None,value=None):
        if evt:
            self.model.checkOverview = evt.IsChecked()
        elif value is not None:
            if self.checkOverview.IsChecked() != value:
                self.checkOverview.SetValue(value)
            if not value:
                self.model.checkMap = False
    def __checkTiles(self,evtName=None,evt=None,value=None):
        if evt:
            self.model.checkTiles = evt.IsChecked()
        elif value is not None:
            if self.checkTiles.IsChecked() != value:
                self.checkTiles.SetValue(value)
    def __dataFile(self,evtName=None,evt=None,value=None):
        if evtName is not None:
            if evtName == 'OnText':
                if self.model.mapConfig != self.DATA.GetValue():
                    self.model.mapConfig = self.DATA.GetValue()
            elif evtName == 'OnButton':
                filter = 'Map Config (*.yaml)|.yaml'
                fileDialog = wx.FileDialog(self,message='Choose Map Config File',wildcard=filter)
                result = fileDialog.ShowModal()
                if result == wx.ID_OK:
                    self.model.mapConfig = fileDialog.GetPath()
                else:
                    print "canceled"
        elif value is not None:
            if value == False:
                pass
            else:
                if not value == self.DATA.GetValue():
                    self.DATA.SetValue(value)
                

