# unit-test生成准则

## DUT

### 文件结构
submodule的定义：我们认为是一个有完整的接口定义的，这个接口定义完备到，我们足以写一个标准的功能函数来生成黄金测试对照模版。
IP是可复用的submodule。
guidance则是常用的几种数据同步方式的设计参考与测试。

## 测试框架

driver生成激励，`check(raw)`检测每一个敏感snapshot的正确性。

driver首先会有一个不断自增的counter，我们会有一个count数字和激励输入的对照关系。由此，我们便可以得到，count和我们通过纯标准黄金功能函数得到的黄金输出的一一对应关系。

driver会把数据push给fifo接口模块，接口模块pop出的data作为value返回传递给downstream模块。

在downstream内，DUT作为external source被实例化。


## driver模板

算术模块测试应尽可能确保对边缘情况的覆盖。并且确保ref model对数据类型的正确处理。

````python
class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, forward1: Module, forward2: Module):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)
        add_in1 = cnt[0].case({
            UInt(32)(0): Int(32)(-100).bitcast(UInt(32)),
            UInt(32)(1): Int(32)(0).bitcast(UInt(32)),
            UInt(32)(2): Int(32)(100).bitcast(UInt(32)),
            None: cnt[0],
        })
        add_in2 = cnt[0].case({
            UInt(32)(0): Int(32)(100).bitcast(UInt(32)),
            UInt(32)(1): Int(32)(-100).bitcast(UInt(32)),
            UInt(32)(2): Int(32)(-1).bitcast(UInt(32)),
            None: cnt[0],
        })

        forward1.async_called(data=add_in1)
        forward2.async_called(data=add_in2)

````

### Uint Adder



### FSM
一个常见的时序逻辑测试场景是 Moore FSM。

我们在需求中已描述了所关心的状态转移条件与状态输出。

### 复杂Decoding

比如CPU的decoding，我们会有一个复杂的映射表格来对照。
