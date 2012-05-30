import wx
from model import M_DyMaps2
from rc import DyMaps_xrc
import inspect
import types
from StringIO import StringIO
import yaml
import os.path

from wxpysal.util.progressDialog import ProgressDialog
from uploadControl import C_UploadTiles



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
            if type(obj) == types.MethodType and inspect.getargspec(obj)[0] == ['self', 'evt']:
                #print "remapping instance.%s(evt) to instance.dispatch('%s',evt)"%(name,name)
                setattr(instance,name,evt(dispatcherMethod,name))

class C_DyMaps(DyMaps_xrc.xrcDyMaps):
    """Implements the DyMaps Frame"""
    def __init__(self,parent=None):
        remapEvtsToDispatcher(self,self.evtDispatch)
        DyMaps_xrc.xrcDyMaps.__init__(self,parent)

        self.mapBitmap = wx.StaticBitmap(self.mapPanel)
        self.path = False
    
        ### Dispatch should contian both model tags (model.TAGS), and widgetNames.
        self.dispatch = d = {}
        d['geoData'] = self.__dataFile
        d['dataFile'] = self.__dataFile
        d['fileopenbutton'] = self.__dataFile
        d['mapPng'] = self.__drawMap
        d['variableNames'] = self.__vars
        d['idVariable'] = self.__vars
        d['varsChoice'] = self.__vars
        d['mapScales'] = self.__mapScales
        d['scalesChoice'] = self.__scales
        d['scales'] = self.__scales
        d['ToolNew'] = self.new
        d['ToolOpen'] = self.open
        d['ToolSave'] = self.save
        d['ButtonSave'] = self.save
        d['ToolSaveAs'] = self.saveAs
        d['NotesTextCtrl'] = self.__notes #Notes: wxWidget
        d['notes'] = self.__notes #Notes: model property
        d['SourceTextCtrl'] = self.__source
        d['source'] = self.__source
        d['NameTextCtrl'] = self.__name
        d['name'] = self.__name
        d['Close'] = self.OnClose
        d['ButtonRender'] = self.run
        d['cacheFile'] = self.__cacheFile
        d['ButtonCache'] = self.__cacheFile
        d['ButtonSaveMS'] = self.__save_to_ms
        d['ButtonUpload'] = self.__upload

        self.model = M_DyMaps2()
        self.model.addListener(self.populate)
        self.model.size = self.mapPanel.GetSize()
        self.cacheWarn.Hide()


    def reset(self):
        self.model.reset()
        self.model.size = self.mapPanel.GetSize()
    def ZoomLevelMouse(self,evt):
        if evt.EventType == wx.EVT_LEAVE_WINDOW.typeId:
            print "Mouse is gone, restore map"
        elif evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            print "motion"
            print evt.GetEventObject()
        evt.Skip()
    def OnClose(self,*args):
        if self.confirm():
            self.Destroy()
    def OnPaint(self,evt):
        self.model.size = self.mapPanel.GetSize()
        evt.Skip()
    def OnSize(self,evt):
        self.model.size = self.mapPanel.GetSize()
        evt.Skip()
    def confirm(self):
        """ Prevent the model from being lost, prompts the user to save model if it has been modified"""
        if self.model.IsModified():
            confirmDialog = wx.MessageDialog(self,"You changes will be lost of you don't save them.",'Do you want to save the changes you made?',style=wx.YES_NO|wx.CANCEL|wx.CENTRE)
            result = confirmDialog.ShowModal()
            if result == wx.ID_YES:
                self.save()
                return True
            elif result == wx.ID_NO:
                return True
            else:
                return False
        return True

    def evtDispatch(self,evtName,evt):
        evtName,widgetName = evtName.split('_',1)
        if widgetName in self.dispatch:
            self.dispatch[widgetName](evtName,evt)
        else:
            print "not implemneted:",evtName,widgetName
        #print evtName,widgetName
    def new(self,evtName=None,evt=None):
        if self.confirm():
            self.reset()
            self.path = False
            self.populate()
    def open(self,evtName=None,evt=None):
        if self.confirm():
            pass
        else:
            return
        filter = "Map Configuration File (*.yaml)|*.yaml"
        fileDialog = wx.FileDialog(self,message="Select Map Configuration",wildcard=filter)
        result = fileDialog.ShowModal()
        if result == wx.ID_OK:
            path = fileDialog.GetPath()
            f = open(path,'r')
            m = yaml.load(f)
            if isinstance(m,M_DyMaps2):
                self.path = path
                self.model = m
                self.model.size = self.mapPanel.GetSize()
                self.model.addListener(self.populate)
                self.model.SetModified(False)
                self.populate()
                self.model.SetModified(False)
                self.title()
            else:
                raise TypeError,'YAML file is not of type M_DyMaps2'
    def __save_to_ms(self,evtName=None,evt=None):
        dirDialog = wx.DirDialog(self,message="Please select a location to save tile server files.")
        result = dirDialog.ShowModal()
        if result == wx.ID_OK:
            path = dirDialog.GetPath()
            self.model.save_to_ms(path)
        
    def saveAs(self,evtName=None,evt=None):
        filter = "Map Configuration File (*.yaml)|*.yaml"
        fileDialog = wx.FileDialog(self,message="Save Map Configuration",wildcard=filter,style=wx.SAVE+wx.OVERWRITE_PROMPT)
        result = fileDialog.ShowModal()
        if result == wx.ID_OK:
            path = fileDialog.GetPath()
            if path[-5:].lower() != '.yaml':
                path += '.yaml'
            self.path = path
            return self.save()
            #return True
        else:
            return False
    def save(self,evtName=None,evt=None):
        if self.path:
            f = open(self.path,'w')
            f.write(yaml.dump(self.model))
            f.close()
            self.title()
            return True
        else:
            return self.saveAs()
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
        self.title()
    def title(self,default="Untitled"):
        if self.path:
            fName = os.path.basename(self.path)
            self.SetTitle(fName)
        else:
            self.SetTitle(default)
        if self.model.IsModified():
            self.SetTitle(self.GetTitle()+'*')
        else:
            self.SetTitle(self.GetTitle().replace('*',''))

    def run(self,evtName=None,evt=None):
        if not self.model.verify():
            fail = wx.MessageDialog(self,"Please be sure you have selected a valid ShapeFile, ID Variable and enabled at least one Zoom Level. Also check that you have selected a valid cache location.",'Not Ready to Render!',style=wx.OK|wx.CENTRE|wx.ICON_INFORMATION)
            fail.ShowModal()
            return False
        if self.save():
            mapScales = self.model.mapScales
            #tiles,numTiles = self.model.tilesToCache()
            numTiles = sum([mapScales[i][1] for i in self.model.scales])
            #cacheSize = self.model.cacheSize
            #if cacheSize > 0 :
            #    numTiles = sum(numTiles) - self.model.cacheSize
            #else:
            #    numTiles = sum(numTiles)
            #if numTiles == 0:
            #    msg = wx.MessageDialog(self,"All tiles have been rendered. If you want to re-render everything please delete you cache file: %s"%self.model.cacheFile,'Nothing Left To Render!',style=wx.OK|wx.CENTRE|wx.ICON_INFORMATION)
            #    msg.ShowModal()
            #    return

            path = self.path
            #class myProgressDialog(ProgressDialog):
            #    def message(self):
            #        return "Tile %d of %d"%(self.counter,self.max)
            #progress = ProgressDialog('Render Status','%d tiles will be rendered!'%numTiles,maximum=numTiles,parent=self,style=wx.PD_APP_MODAL|wx.PD_CAN_ABORT|wx.PD_AUTO_HIDE)
            progress = ProgressDialog('Render Status','%d tiles will be rendered!'%numTiles,maximum=numTiles,parent=self,style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
            progress.SetSize((400,-1))
            progress.Show()
            result = self.model.run(pulse=progress.pulse)
            if result:
                success = wx.MessageDialog(self,"Results have been saved in %s"%(os.path.basename(self.model.cacheFile)),'Success!',style=wx.OK|wx.CENTRE|wx.ICON_INFORMATION)
                success.ShowModal()
        
    def able(self):
        pass
    def __dataFile(self,evtName=None,evt=None,value=None):
        if evtName != None:
            if evtName == 'OnText':
                if self.model.geoData != self.dataFile.GetValue():
                    self.model.geoData = self.dataFile.GetValue()
            elif evtName == 'OnButton':
                filter = "Shape File (*.shp)|*.shp"
                fileDialog = wx.FileDialog(self,message="Choose Shape File",wildcard=filter)
                result = fileDialog.ShowModal()
                if result == wx.ID_OK:
                    self.model.geoData = fileDialog.GetPath()
                else:
                    print "canceled"
        elif value != None:
            if value == False:
                pass
                #print "warning datafile"
                #self.dataFileWarn.Show()
            else:
                if not value == self.dataFile.GetValue():
                    self.dataFile.SetValue(value)
                #self.dataFileWarn.Hide()
    def __drawMap(self,value=None):
        if value == '':
            #w,h = self.mapBitmap.GetSizeTuple()
            w,h = 1,1
            img  = wx.EmptyImage(w,h)
            img.SetData(buffer('\xff'*w*h*3))
            bitmap = wx.BitmapFromImage(img)
            self.mapBitmap.SetBitmap(bitmap)
        elif value != None:
            img = wx.ImageFromStream(StringIO(value))
            bitmap = wx.BitmapFromImage(img)
            self.mapBitmap.SetBitmap(bitmap)
    def __vars(self,evtName=None,evt=None,value=None):
        if evt != None: #evt fired
            old_value = self.model.idVariable
            value = self.varsChoice.GetSelection()
            if not old_value == value:
                self.model.idVariable = value
                self.model.update('mapPng') #force trigger a map update
        elif value == '':
            self.varsChoice.Clear()
        elif value != None: #model changed
            if type(value) == int:
                self.varsChoice.SetSelection(value)
            else:
                self.varsChoice.Clear()
                if '' in value:
                    value.remove('')
                self.varsChoice.AppendItems(value)
    def __mapScales(self,evtName=None,evt=None,value=None):
        if value == '':
            self.scalesChoice.Clear()
        elif value != None:
            self.scalesChoice.Clear()
            scales = ["Zoom Level %d: %d Tiles"%(scale[0],scale[1]) for scale in value]
            #scales = ["Zoom Level %d: %d Tiles"%(scale[0],scale[1]) for scale in self.model.mapScales]
            self.scalesChoice.AppendItems(scales)
    def __scales(self,evtName=None,evt=None,value=None):
        if evtName == 'OnChoice':
            self.model.scales = range(self.scalesChoice.GetSelection()+1)
            #self.model.checkCache()
        if value == '':
            value = tuple()
        if value != None:
            self.scalesChoice.SetSelection(value[-1])
    def __notes(self,evtName=None,evt=None,value=None):
        if evt != None and self.model.notes != self.NotesTextCtrl.GetValue():
            self.model.notes = self.NotesTextCtrl.GetValue()
        elif value != None:
            self.NotesTextCtrl.SetValue(value)
    def __source(self,evtName=None,evt=None,value=None):
        if evt != None and self.model.source != self.SourceTextCtrl.GetValue():
            self.model.source = self.SourceTextCtrl.GetValue()
        elif value != None:
            self.SourceTextCtrl.SetValue(value)
    def __name(self,evtName=None,evt=None,value=None):
        if evt != None and self.model.name != self.NameTextCtrl.GetValue():
            self.model.name = self.NameTextCtrl.GetValue()
        elif value != None:
            self.NameTextCtrl.SetValue(value)
    def __cacheFile(self,evtName=None,evt=None,value=None):
        if evtName != None:
            if evtName == 'OnText':
                if self.model.cacheFile != self.cacheFile.GetValue():
                    self.model.cacheFile = self.cacheFile.GetValue()
            elif evtName == 'OnButton':
                filter = "Cache File (*.csv)|*.csv"
                fileDialog = wx.FileDialog(self,message="Choose Cache File",wildcard=filter,style=wx.FD_SAVE)
                result = fileDialog.ShowModal()
                if result == wx.ID_OK:
                    self.model.cacheFile = fileDialog.GetPath()
                else:
                    print "canceled"
        elif value != None:
            if value == False:
                pass
                #self.cacheFileWarn.Show()
            else:
                if not value == self.cacheFile.GetValue():
                    self.cacheFile.SetValue(value)
                #self.cacheFileWarn.Hide()
    def __upload(self,evtName=None,evt=None,value=None):
        if evtName == 'OnButton':
            frame = C_UploadTiles(self,self.path)
            frame.ShowModal()
        elif value != None:
            print value
