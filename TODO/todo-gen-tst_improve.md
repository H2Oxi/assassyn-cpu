# todo

oct,25,15:00,tbd

## 

1. 规划一个通用的stimulus模版，把driver每次写test的代码复杂度降低

2. 规划一个具有普适性的模版,现在LLM生成的check raw的抓取逻辑有一点不统一，请统计不同的场景下的需求，我们需要提供一个统一的参考模版。

## 

请根据下面的几种典型的使用场景，设计一个比较通用的验证辅助接口函数。这个验证接口函数最后将会以check(raw)的形式被使用。

需要支持的模块类型：

`test/hw/unit-test/guide/fsm.py`,这种有内部状态的显式模块
`test/hw/unit-test/ip/test_regfile.py` 有时序要求的外部模块
`test/hw/unit-test/ip/test_adder.py` 简单的组合逻辑模块
`test/sw/test_decoder.py` 复杂抓取的组合逻辑模块