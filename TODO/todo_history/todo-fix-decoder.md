# todo

oct,24,22:30,tbd

## 修复decoder端口冗余

1. 请规划如何把`impl/external_src/ins_decoder.sv`中imm相关的输出精简成1个统一的输出, 需要在`impl/gen_cpu/submodules.py`同步更新对应的端口,可以参考`docs/rv32i.csv`来确认我们需要支持的所有指令。更新对应文件。

2. 在done文档中规划输出如何和`impl/ip/ips.py`中的ip进行对接。