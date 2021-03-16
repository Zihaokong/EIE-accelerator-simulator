from module import BaseModule
from component import *
from config import *
import os
from enum import Enum

Activations_k = 0
Bias1_k = 1
Empty_k = 2

class ActsRW(BaseModule):
    def __init__(self,filename):
        super().__init__()
        self.name = "Activation Read/Write"

        # To Nonzero fetch Registers
        self.read_addr_reg = Register(name="read_addr_reg")
        self.end_addr_reg = Register(name="end_addr_reg")
        self.which = Register(name="which")
        self.internal_state = Register(name="internal_state")
        self.has_bias = Register(name='has_bias')

        # Wire
        self.reg_addr_w = Wire(name="reg_addr_w")
        self.read_addr_reg_D = Wire(name="read_addr_reg_D")
        self.internal_state_D = Wire(name="internal_state_D")
        self.acts_per_bank = Wire(width=NUM_PE,name="acts_per_bank")

        # Shared Wire
        self.next_reg_addr = None



        # To Arithmetic module
        for i in range(NUM_PE):
            self.__setattr__("read_addr_arithm_"+str(i),Wire(name="read_addr_arithm_"+str(i)))
            self.__setattr__("write_addr_arithm_" + str(i),
                             Wire(name="write_addr_arithm_" + str(i)))
            self.__setattr__("write_data_arithm_" + str(i),
                             Wire(name="write_data_arithm_" + str(i)))
            self.__setattr__("write_enable_" + str(i),
                            Wire(name="write_enable_D_" + str(i)))

            self.__setattr__("read_data_arithm_"+str(i),Wire(name="read_data_arithm_"+str(i)))


        # Wire
        self.write_complete = Wire(name="write_complete")
        self.layer_complete = Wire(name="layer_complete")


        self.bank_size = (ACTRW_maxcapacity - 1) // NUM_PE + 1
        self.memory_size = self.bank_size * NUM_PE
        self.ACTmem = [Memory(name="ACTmem0", size=self.memory_size),Memory(name="ACTmem1", size=self.memory_size)]


        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                flt = []
                values = f.read().split()
                for i in values:
                    flt.append(float(i))
                ind = 0
                for i in flt:
                    self.ACTmem[self.which.data].data[ind] = flt[ind]
                    ind+=1




            # with open(filename, 'r') as f:
            #     values = f.read().splitlines()
            #     for i in range(0, len(values)):
            #         self.ACTmem[self.which.data].data[i] = int(values[i])
            print("[ACTRW: activation init success]")
            print("Length:",len(self.ACTmem[0].data),self.ACTmem[0].data)
            print("Length:",len(self.ACTmem[1].data),self.ACTmem[1].data)
        self.activation_length = len(flt)
    def set_state(self, input_size_t, which_t, bias_t):
        self.which.data = which_t
        self.has_bias.data = bias_t
        if input_size_t > ACTRW_maxcapacity:
            print("Error: End address exceeds memory capacity")

        self.end_addr_reg.data = (input_size_t - 1) // NUM_PE

    def connect(self, dependency):
        if dependency.getName() == "Non-Zero Fetch":
            self.next_reg_addr = dependency.next_reg_addr
            dependency.next_reg_addr.shared = True
            print("[ACTRW: CONNECTIONS SUCCESS TO:",dependency.getName(),"]")
        elif dependency.getName() == "Arithm Unit":

            self.__setattr__("read_addr_arithm_D_" + str(dependency.getId()),dependency.read_addr)
            dependency.read_addr.shared = True

            self.__setattr__("write_addr_arithm_D_" + str(dependency.getId()), dependency.write_addr)
            dependency.write_addr.shared = True

            self.__setattr__("write_data_arithm_D_" + str(dependency.getId()), dependency.write_data)
            dependency.write_data.shared = True

            self.__setattr__("write_enable_D_" + str(dependency.getId()), dependency.write_enable)
            dependency.write_enable.data = True

            print("[ACTRW: CONNECTIONS SUCCESS TO:", dependency.getName(),dependency.getId(), "]")
        else:
            print("Error: Unknown module type!")

    def propagate(self):
        nzf_id = self.which.data
        arithm_id = 1 - self.which.data

        if self.internal_state.data == Activations_k:
            for i in range(NUM_PE):
                self.acts_per_bank.data[i] = self.ACTmem[nzf_id].data[self.read_addr_reg.data * NUM_PE + i]

                self.reg_addr_w.data = self.read_addr_reg.data
                self.read_addr_reg_D.data = self.read_addr_reg.data + 1

                next_state = 0
                if self.has_bias.data == 1:
                    next_state = Bias1_k
                else:
                    next_state = Empty_k

                if self.read_addr_reg.data == self.end_addr_reg.data:
                    self.internal_state_D.data = next_state
                else:
                    self.internal_state_D.data = Activations_k


            if DEBUG == 1:
                print("[ACTRW: activation send:",self.acts_per_bank.data,"reg_addr is:",self.reg_addr_w.data,"]")

        elif self.internal_state.data == Bias1_k:


            for i in range(NUM_PE):
                self.acts_per_bank.data[i] = 0

            self.acts_per_bank.data[0] = 1
            self.reg_addr_w.data = self.end_addr_reg.data + 1
            self.read_addr_reg_D.data = 0
            self.internal_state_D.data = Empty_k

            if DEBUG == 1:
                print("[ACTRW: Bias State, send: ", self.acts_per_bank.data, "reg_addr is", self.reg_addr_w.data, "]")


        elif self.internal_state.data == Empty_k:
            for i in range(NUM_PE):
                self.acts_per_bank.data[i] = 0

            self.reg_addr_w.data = 0
            self.read_addr_reg_D.data = 0
            self.internal_state_D.data = Empty_k

            if DEBUG == 1:
                print("[ACTRW: Empty State]")

        else:
            print("Error: unknown state")

        print("ACTIVATION STATE:",self.internal_state)

        self.write_complete.data = 1
        for i in range(NUM_PE):
            read_result = self.ACTmem[arithm_id].data[self.__getattribute__("read_addr_arithm_"+str(i)).data * NUM_PE + i]
            output = self.__getattribute__("read_data_arithm_"+str(i))
            output.data = read_result

            self.write_complete.data = int(self.write_complete.data and (not self.__getattribute__("write_enable_"+str(i)).data))

        self.layer_complete.data = int(self.write_complete.data and (self.internal_state.data == Empty_k))

        if DEBUG:
            print("[ACTRW: incoming write_enable_D",self.__getattribute__("write_enable_D_"+str(i)).data,"]")

    def update(self):
        arithm_id = 1 - self.which.data

        if self.next_reg_addr.data == 1:
            self.read_addr_reg.data = self.read_addr_reg_D.data
            self.internal_state.data = self.internal_state_D.data

            if DEBUG == 1:
                print("[ACTRW: now read address:",self.read_addr_reg.data,"next state is:",self.internal_state.data,"]")


        for i in range(NUM_PE):

            if self.__getattribute__("write_enable_D_"+str(i)).data == 1:
                mem_index = self.__getattribute__("write_addr_arithm_D_"+str(i)).data * NUM_PE + i
                self.ACTmem[arithm_id].data[mem_index] = self.__getattribute__("write_data_arithm_D_"+str(i)).data

                if DEBUG:
                    print("[ACTRW: write finished!]")

            self.__getattribute__("read_addr_arithm_" + str(i)).data = self.__getattribute__(
                "read_addr_arithm_D_" + str(i)).data
            self.__getattribute__("write_data_arithm_" + str(i)).data = self.__getattribute__(
                "write_data_arithm_D_" + str(i)).data
            self.__getattribute__("write_addr_arithm_" + str(i)).data = self.__getattribute__(
                "write_addr_arithm_D_" + str(i)).data
            self.__getattribute__("write_enable_" + str(i)).data = self.__getattribute__(
                "write_enable_D_" + str(i)).data



    def getattr(self,stringName):
        return self.__getattribute__(stringName)