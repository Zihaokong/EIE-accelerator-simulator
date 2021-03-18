from component import  *
from module import *
from ptrvec import *
from spmat import *
from Nzerofetch import *
from ActsRW import *
from arithm import *

def assemble(folderpath,NUM_PE,cycle):
    ptr = []
    spm = []
    ari = []


    acts = ActsRW(folderpath+"/act.dat")
    print("Activation length:",acts.activation_length)
    acts.set_state(acts.activation_length,0,1)

    nzero = NzeroFetch()

    for i in range(NUM_PE):
        ptr.append(PtrRead(folderpath+"/ptr/ptr"+str(i)+".dat",i))
        spm.append(SpMatRead(folderpath+"/spm/spm"+str(i)+".dat", i))
        ari.append(ArithmUnit(folderpath+"/arithm.dat", i))

    for i in range(len(ptr)):
        ptr[i].connect(nzero)

    for i in range(len(spm)):
        spm[i].connect(ptr[i])

    for i in range(len(ari)):
        ari[i].connect(spm[i])
        ari[i].connect(acts)

    for i in range(len(ari)):
        acts.connect(ari[i])
        nzero.connect(ptr[i])

    acts.connect(nzero)
    nzero.connect(acts)

    j = 0
    while acts.layer_complete.data != 1:
        print("cycle", j)
        print("----propagate----")
        for i in range(len(ptr)):
            ptr[i].propagate()
            spm[i].propagate()
            ari[i].propagate()
        acts.propagate()
        nzero.propagate()
        print("----update----")
        for i in range(len(ptr)):
            ptr[i].update()
            spm[i].update()
            ari[i].update()
        acts.update()
        nzero.update()
        print(acts.layer_complete)
        print("\n")
        j+=1
    return acts.ACTmem[1].data
def print_layer_info(filename,NUM_PE):
    print("[Start processing:",filename,"]")

    activation_dir = filename+"/act.dat"
    if os.path.isfile(activation_dir):
        with open(activation_dir, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i))
            ind = 0
            print("[Activation length is",len(flt),"]")

    spm_dir = filename+"/spm/spm0.dat"
    if os.path.isfile(spm_dir):
        with open(spm_dir, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i[0:-1]))
            ind = 0
            print("[One PE stores:",len(flt)//2,"number of encoded weights, total number of weights: is approximately",len(flt)//2 * NUM_PE,"]")

    ptr_dir = filename+"/ptr/ptr0.dat"
    if os.path.isfile(ptr_dir):
        with open(ptr_dir, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i[0:-1]))
            ind = 0
            print("[Layer has",len(flt)-1,"columns, including bias term]")

    codebook_dir = filename+"/arithm.dat"
    if os.path.isfile(codebook_dir):
        with open(codebook_dir, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i))
            ind = 0
            print("[codebook is has",len(flt),"entries,",flt,"]")

    ground_truth_dir = filename+"/groundtruth.dat"
    output = []
    output_len = 0
    if os.path.isfile(ground_truth_dir):
        with open(ground_truth_dir, 'r') as f:
            flt = []
            values = f.read().split()
            for i in values:
                flt.append(float(i))
            output = flt
            ind = 0
            print("[Output after Relu has",len(flt),"entries]")
            output_len = len(flt)
    print(output[0:100])
    return output,output_len
def main():
    filename = "./vgg16-fc7.tar"
    outputus = assemble(filename,NUM_PE,100000)
    output,output_len = print_layer_info(filename,NUM_PE)
    print("Raw output  :",outputus[0:output_len])
    print("Ground truth:", output)
    for i in range(len(outputus)):
        if outputus[i] <0:
            outputus[i] = 0.0
    print("Our RElu    :",outputus[0:output_len])

    f = open(filename+"-output.txt", "w")
    f.write(str(outputus[0:output_len]))

if __name__ == '__main__':
    main()
