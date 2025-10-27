# todo

oct,25,13:00,tbd

## 生成decoding test

1. 请参考`assassyn/python/ci-tests/test_sram.py`中关于sram的用法，在`test/sw/test_decoder.py`中对`impl/gen_cpu/dut/decoding.py`进行测试。`Decoder`就相当于此时的memuser，然后我希望你能够使用`resources/riscv/benchmarks/0to100.exe`作为这个sram所存储的指令。然后指令作为`rdata`(array变量)传入decoder，我们来检测每个指令对应的译码输出是否正确。

