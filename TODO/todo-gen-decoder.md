# todo4

oct,23,20:00,tbd

## 设计端口与声明

1. Plan，和我一起规划`ins_decoder`模块的接口设计。首先，我们的输入是rv32i的指令码，我们所需要支持的指令都陈列在了`docs/rv32i.csv`. 首先我们需要确认，要完整的实现对这些指令的支持，我们现有的ip是否足以支持（in `impl/ip/ips.py`）。如果已经足够支持，请根据我们的这几个ip的端口，来设计与之匹配的输出。

2. 根据前面讨论后的端口设计，在`impl/gen_cpu/submodules.py`中对`ins_decoder`模块的`ExternalSV`class声明，可以参考`impl/ip/ips.py`，需要对每个接口进行注释说明。

## 设计迭代

根据前面的端口设计，在`impl/gen_cpu/external_src`创建并撰写`ins_decoder.sv`. 我们可以按照指令种类来进行分类迭代支持。

1. 在`test/hw/ci-test`中，我们需要依次增加支持的指令种类，逐渐完善对decoder的编写和验证。

2. 在`test/hw/unit-test/submodules`创建对这个模块的unit-test，可以参考`test/hw/unit-test/ip/test_adder.py`，请注意`test/hw/unit-test/unit-test.md`要求的设计规范,由于前面已经对五种指令分别依次测试过，因此在unit-test中我们只需要对每一种指令选1-2个典型指令进行测试即可。
