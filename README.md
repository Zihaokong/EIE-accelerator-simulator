# EIE-accelerator-simulator
CSE240D Final projects, this is an reimplementation of paper [EIE: Efficient Inference Engine on Compressed Deep Neural Network](https://arxiv.org/abs/1602.01528) by Song Han and etc. It's a software simulation tool that takes in a CSC form of sparse matrix and run through simulator, producing results.

To run it, type your input file name in `main.py` and run the command `python main.py`

Simulator output is pass through ReLU, which makes all negative entry 0. For checking correctness, you can compare different `output.txt` with `groundtruth.dat` inside each layer directory. **Num of PE** used for simulation is 32 and assuming all the memories in the simulator are big enough to accomodate the entire neural network fully connected layer.

Made by Zihao Kong, Yuan Wang
3/16/2021
