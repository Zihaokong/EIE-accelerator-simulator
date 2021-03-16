from module import BaseModule
from component import *
from config import *
import os


class ArithmUnit(BaseModule):
    def __init__(self, filename: str, value: int):
        super().__init__(value)
        self.name = "Arithm Unit"

        # Phase 1 Registers
        self.patch_complete = Register(name="patch_complete")
        self.index = Register(name="index")
        self.value_code = Register(name="value_code")
        self.act_value = Register(name="act_value")
        self.valid = Register(name="valid")

        # Phase 2 registers
        self.read_addr_last = Register(name="read_addr_last")
        self.read_addr_p = Register(name="read_addr_p")
        self.value_decode = Register(name="value_decode")
        self.act_value_p = Register(name="act_value_p")
        self.valid_p = Register(name="valid_p")

        # Phase 3 Registers
        self.read_data = Register(name="read_data")
        self.result_mul = Register(name="result_mul")
        self.valid_p_p = Register(name="valid_p_p")
        self.read_addr_p_p = Register(name="read_addr_p_p")

        # Wires
        self.read_addr = Wire(name="read_addr")
        self.read_addr_last_D = Wire(name="read_addr_last_D")
        self.value_decode_D = Wire(name="value_decode_D")
        self.value_code_w = Wire(name="value_code_w")
        self.value_to_add = Wire(name="value_to_add")
        self.result_muladd = Wire(name="result_muladd")
        self.result_mul_D = Wire(name="result_mul_D")
        self.bypass = Wire(name="bypass")
        self.write_enable = Wire(name="write_enable")
        self.write_addr = Wire(name="write_addr")
        self.write_data = Wire(name="write_data")
        self.valid_w = Wire(name="valid_w")
        self.valid_p_w = Wire(name="valid_p_w")
        self.read_addr_p_w = Wire(name="read_addr_p_w")
        self.act_value_w = Wire(name="act_value_w")

        self.codebook = [0] * ARITHM_codebooksize

        # Shared Wire
        self.patch_complete_D = None
        self.index_D = None
        self.value_code_D = None
        self.act_value_D = None
        self.valid_D = None
        self.read_data_D = None

        with open(filename, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i))
            for i in range(len(flt)):
                self.codebook[i] = flt[i]
        print('[ARITHM: codebook init success]')
        print("Length:",len(self.codebook),self.codebook)


        # if os.path.isfile(filename):
        #     with open(filename, 'r') as f:
        #         values = f.read().splitlines()
        #         for i in range(0, len(values)):
        #             self.codebook[i] = float(values[i])


    def connect(self, dependency):
        if dependency.getName() == "Sparse Matrix Read" and dependency.getId() == self.getId():
            self.patch_complete_D = dependency.patch_complete_w
            self.index_D = dependency.index
            self.value_code_D = dependency.code
            self.act_value_D = dependency.value_w
            self.valid_D = dependency.valid_w
            print("[ARITHM",self.getId(),": CONNECTION SUCCESS TO:",dependency.getName(),dependency.getId(),"]")
        elif dependency.getName() == "Activation Read/Write":
            self.read_data_D = dependency.getattr("read_data_arithm_"+str(self.getId()))
            print("[ARITHM", self.getId(), ": CONNECTION SUCCESS TO:", dependency.getName(),"]")

    def propagate(self):
        self.read_addr.data = self.index.data + self.read_addr_last.data
        if self.patch_complete.data == 1:
            self.read_addr_last_D.data = 0
        else:
            self.read_addr_last_D.data = self.read_addr.data + 1
        self.value_decode_D.data = self.codebook[self.value_code.data]
        self.value_code_w.data = self.value_code.data
        self.act_value_w.data = self.act_value.data
        self.valid_w.data = self.valid.data

        if DEBUG:
            print("[ARITHM PHASE1 weight is:",self.value_decode_D.data,"activation is:",
              self.act_value_w.data,"dest address is:",self.read_addr.data,"current entry is valid?",self.valid_w.data,"]")
        self.bypass.data = int(self.valid_p_p.data and (self.read_addr_p.data == self.read_addr_p_p.data))
        self.result_mul_D.data = self.value_decode.data * self.act_value_p.data



        self.valid_p_w.data = self.valid_p.data

        if DEBUG:
            print("[ARITHM PHASE2 result is:", self.result_mul_D.data, "from", self.value_decode.data, "*",
                  self.act_value_p.data, "valid?", self.valid_p.data, "]")

        self.read_addr_p_w.data = self.read_addr_p.data

        self.result_muladd.data = self.result_mul.data + self.read_data.data

        self.write_enable.data = self.valid_p_p.data
        self.write_addr.data = self.read_addr_p_p.data
        self.write_data.data = self.result_muladd.data

        if DEBUG:
            print("[ARITHM PHASE3 write data to ACT is",self.result_muladd.data,"read data from ACT:",self.read_data.data,"addr is:",
              self.write_addr.data,"valid entry?",self.write_enable.data,"]")

    def update(self):
        self.patch_complete.data = self.patch_complete_D.data
        self.index.data = self.index_D.data
        self.value_code.data = self.value_code_D.data
        self.act_value.data = self.act_value_D.data
        self.valid.data = self.valid_D.data

        if self.valid_w.data == 1:
            self.read_addr_last.data = self.read_addr_last_D.data
            if DEBUG:
                print("[ARITHM update read_addr_last:",self.read_addr_last.data,"]")


        self.read_addr_p.data = self.read_addr.data
        self.value_decode.data = self.value_decode_D.data
        self.act_value_p.data = self.act_value_w.data

        self.valid_p.data = int(self.valid_w.data)# and (self.value_code_w.data != 0))


        self.read_addr_p_p.data = self.read_addr_p_w.data
        self.result_mul.data = self.result_mul_D.data
        self.valid_p_p.data = self.valid_p_w.data
        if self.bypass.data == 1:
            self.read_data.data = self.write_data.data
        else:
            self.read_data.data = self.read_data_D.data

            if DEBUG:
                print("[ARITHM: accumulate value acquired from ACTRW:",self.read_data.data,"]")
