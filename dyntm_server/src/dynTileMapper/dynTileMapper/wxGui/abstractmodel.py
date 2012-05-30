class AbstractModel(object):
    """ From wxPIA/Chapter-05 """
    def __init__(self):
        self.listeners = []
        self.modified = False

    def addListener(self, listenerFunc):
        self.listeners.append(listenerFunc)

    def removeListener(self, listenerFunc):
        self.listeners.remove(listenerFunc)

    def update(self,tag=None,changeState=True):
        if changeState:
            self.SetModified(True)
        for eachFunc in self.listeners:
            eachFunc(tag)
    def SetModified(self,state):
        self.modified = state
    def IsModified(self):
        return self.modified
