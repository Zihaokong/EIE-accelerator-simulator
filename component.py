class Register:

    def __init__(self, width: int = 1, name: str = "", value: int = 0):
        self.name = name
        self.width = width

        self.prev = ""

        if width == 1:
            self.data = value
        else:
            self.data = [value] * width

    def __str__(self):
        if "[Register: " + str(self.name) + " " + str(self.data) + "]" == self.prev:
            return self.prev
        else:
            self.prev = "[Register: " + str(self.name) + " " + str(self.data) + "]"
            return self.prev + " -- Changed!"

class Wire:
    def __init__(self, shared: bool = False, width: int = 1, name: str = "", value = 0):
        self.name = name
        self.shared = shared
        self.width = width

        self.prev = ""

        if width == 1:
            self.data = value
        else:
            self.data = [value] * width

    def __str__(self):
        if self.shared == True:
            if "[SharedWire: " + str(self.name) + " " + str(self.data) + "]" == self.prev:
                return self.prev
            else:
                self.prev = "[SharedWire: " + str(self.name) + " " + str(self.data) + "]"
                return self.prev + " -- Changed!"

        else:
            if "[Wire: " + str(self.name) + " " + str(self.data) + "]" == self.prev:
                return self.prev
            else:
                self.prev = "[Wire: " + str(self.name) + " " + str(self.data) + "]"
                return self.prev + " -- Changed!"


class Memory:
    def __init__(self, name: str = "", size: int = 0):
        self.name = name
        self.data = [0] * size

    def __add__(self, other):
        self.data += other
        return self.data

    def show(self, start, end):
        for i in range(start,end):
            print(self.data[i])