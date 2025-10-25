# todo

oct,24,23:00,tbd

## 使用record语法来使用ins_decoder

1. 在`impl/gen_cpu/pipestage.py`中的`Decoder.build()`内，实例化使用 `impl/gen_cpu/submodules.py`中的`InsDecoder`.使用externalsv的方式可以参考`test/hw/unit-test/ip/test_adder.py`。

2. 请在`assassyn`下查找确认`Record`相关的语法，利用这个语法，结构清晰的组织`InsDecoder`实例化后的输出变量，作为`Decoder.build()`的返回值

