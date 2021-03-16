from component import *
from config import *
import os

class BaseModule:
    module_id = 0
    def __init__(self, id = 0):
        self.module_id = id
        self.name = "Base Module"
    def init(self):
        pass

    def propagate(self):
        pass

    def update(self):
        pass

    def connect(self, dependency):
        pass

    def getName(self):
        return self.name

    def getId(self):
        return self.module_id

    # For debugging, show all register values and names
    def showRegs(self):
        print("---" + self.getName() + "---")
        vv = list(vars(self).values())
        for i in vv:
            if type(i) is type(Register()):
                print(i)

    # For debugging, show all shared wires values and names
    def showSharedWires(self):
        print("---" + self.getName() + "---")
        vv = list(vars(self).values())
        for i in vv:
            if type(i) is type(Wire()):
                if i.shared == True:
                    print(i)

    # For debugging, show all wires values and names
    def showWires(self):
        print("---" + self.getName() + "---")
        vv = list(vars(self).values())
        for i in vv:
            if type(i) is type(Wire()):
                print(i)

    def showConnectionWires(self):
        pass

    def __str__(self):
        return "[Module: " + str(self.getName()) + "; id = "+ str(self.getId()) +"]"






