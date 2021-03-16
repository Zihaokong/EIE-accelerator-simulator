from module import BaseModule
from component import *
from config import *
import os


class PtrRead(BaseModule):
    def __init__(self, filename: str, value: int):

        self.num_lines = PTRVEC_num_lines
        self.unit_line = SPMAT_unit_line

        super().__init__(value)
        self.name = "Pointer Read Unit"
        # Registers
        self.ptr_odd_addr = Register(name="ptr_odd_addr", value=0)
        self.ptr_even_addr = Register(name="ptr_even_addr", value=0)
        self.index_flag = Register(name="index_flag", value=0)
        self.value = Register(name="value", value=0)
        self.empty = Register(name="empty", value=1)
        self.read_enable = Register(name="read_enable", value=0)

        # Wires
        self.start_addr = Wire(name="start_addr")
        self.end_addr = Wire(name="end_addr")
        self.valid = Wire(name="valid")
        self.value_w = Wire(name="value_w")
        self.index_odd = Wire(name="index_odd")
        self.index_even = Wire(name="index_even")

        # Registers
        self.start_addr_p = Register(name="start_addr_p", value=0)
        self.memory_addr_p = Register(name="memory_addr_p", value=255)
        self.patch_complete_p = Register(name="patch_complete_p", value=1)

        # Wires
        self.patch_complete = Wire(name="patch_complete")
        self.read_ptr = Wire(name="read_ptr")
        self.read_spmat = Wire(name="read_spmat")
        self.current_addr = Wire(name="current_addr")
        self.memory_addr = Wire(name="memory_addr")
        self.memory_shift = Wire(name="memory_shift")

        # SharedWires
        self.ptr_odd_addr_D = None
        self.ptr_even_addr_D = None
        self.index_flag_D = None
        self.value_D = None
        self.empty_D = None

        # Memory
        self.PTRmem = Memory("PTRmem", PTRVEC_num_lines)

        # Read value from file
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                flt = []
                values = f.read().split()

                for i in values:
                    flt.append(int(i[0:-1]))

                ind = 0
                for i in flt:
                    self.PTRmem.data[ind] = i
                    ind += 1
            print("Length:", len(flt), self.PTRmem.data[len(flt)-1])
            print("[PTR READ mem init success]")
        # if os.path.isfile(filename):
        #     with open(filename, "r") as f:
        #         values = f.read().splitlines()
        #         for i in range(0, len(values)):
        #             self.PTRmem.data[i] = int(values[i])



    def connect(self, dependency: BaseModule):

        """
            Pointer Read Module connects to Non Zero fetch Unit
            Getting a pair of even and odd addresses to Column Pointer memory
            value_D is current activation value
            empty_D is if current activation is empty
            index_flag is for distinguish even and odd address to be start and end address.
        """
        if dependency.getName() == "Non-Zero Fetch":
            self.ptr_odd_addr_D = dependency.ptr_odd_addr
            dependency.ptr_odd_addr.shared = True
            self.ptr_even_addr_D = dependency.ptr_even_addr
            dependency.ptr_even_addr.shared = True
            self.index_flag_D = dependency.index_flag
            dependency.index_flag.shared = True
            self.value_D = dependency.value_output
            dependency.value_output.shared = True
            self.empty_D = dependency.empty
            dependency.empty.shared = True
            print("[PTR READ: CONNECTION SUCCESS TO:",dependency.getName(),"]")
        else:
            print("Error: Connection Error")

    def propagate(self):
        # if current read enable register is true, use odd and even address from Non zero fetch unit to
        # acquire start and end addresses from pointer memory
        if self.read_enable.data == 1:
            self.index_odd.data = self.PTRmem.data[self.ptr_odd_addr.data * 2 + 1]
            self.index_even.data = self.PTRmem.data[self.ptr_even_addr.data * 2]

        if self.index_flag.data == 1:
            self.start_addr.data = self.index_odd.data
            self.end_addr.data = self.index_even.data - 1
        else:
            self.start_addr.data = self.index_even.data
            self.end_addr.data = self.index_odd.data - 1


        # If current entry is empty or index even is equal to index odd, current activation is not valid
        self.valid.data = int(not ((self.index_even.data == self.index_odd.data) or self.empty.data))

        if DEBUG == 1:
            if self.read_enable.data == 1:
                print("[PTR READ: read_enable",self.read_enable.data,"start mem addr is:",self.start_addr.data,"end mem addr is:",self.end_addr.data,"]")
            else:
                print("[PTR READ: read enable is false, do not read from Nzero fetch]")

            if self.valid.data == 1:
                print("[PTR READ: current value,",self.value.data,"is valid]")
            else:
                print("[PTR READ: current value,",self.value.data,"is not valid]")

        # Forward the activation value
        self.value_w.data = self.value.data

        # If all of the weights are read out, then reset current address to start pointer memory address
        # else current address is last current address + 1
        if self.patch_complete_p.data == 1:
            self.current_addr.data = self.start_addr.data
        else:
            self.current_addr.data = self.start_addr_p.data

        # Which line of memory
        self.memory_addr.data = self.current_addr.data // self.unit_line

        # Which entry offset of memory (8 bit per memory entry)
        self.memory_shift.data = self.current_addr.data % self.unit_line

        # whether we should read a new line of memory from weight matrix in next module
        # when we read the last entry in a line and we need more entry in next line and current memory access
        # is valid, we acquire a new line of memory
        self.read_spmat.data = int((self.memory_addr.data != self.memory_addr_p.data) and self.valid.data)

        # if current address is the end, then we finish a patch
        self.patch_complete.data = int(self.current_addr.data == self.end_addr.data)

        # if we finish a patch or current entry is not valid, we acquire a new
        # even and odd index pairs from Non Zero Fetch Unit
        self.read_ptr.data = int((not self.valid.data) or self.patch_complete.data)

        if DEBUG == 1:
            print("[PTR READ: memory address:", self.memory_addr.data, "mem offset is: ", self.memory_shift.data, "if read new block? ",self.read_spmat.data,"]")
            if self.read_ptr.data == 1:
                print("[PTR READ: read more activation from NZERO FETCH]")
            if self.patch_complete.data:
                print("[PTR READ: current patch is completed]")



    def update(self):
        # Only read index pointers when we need index pointers and next activation value is not empty
        self.read_enable.data = int(self.read_ptr.data and (not self.empty_D.data[self.getId()]))
        if DEBUG:
            print("[PTR READ: read from Nzero fetch?",self.read_enable.data,"]")

        # read a new set of odd and even index pointers and activation value
        if self.read_ptr.data == 1:
            if self.empty_D.data[self.getId()] == 0:
                self.ptr_odd_addr.data = self.ptr_odd_addr_D.data[self.getId()]
                self.ptr_even_addr.data = self.ptr_even_addr_D.data[self.getId()]
                self.index_flag.data = self.index_flag_D.data[self.getId()]
                self.value.data = self.value_D.data[self.getId()]

                if DEBUG == 1:
                    print("[PTR READ: successful read from NZERO fetch, value:",self.value.data,"]")

            self.empty.data = self.empty_D.data[self.getId()]
        # If current entry is valid, we keep reading sparse matrix memory, update the
        # read status
        if self.valid.data == 1:
            self.start_addr_p.data = self.current_addr.data + 1
            self.patch_complete_p.data = self.patch_complete.data
            self.memory_addr_p.data = self.memory_addr.data

            if DEBUG:
                print("[PTR READ: update start address, patch_complete status]")



