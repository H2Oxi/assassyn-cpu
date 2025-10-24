# ci-test生成准则

## DUT

首先，需要明确的是，ci-test首先要遵循和`test/hw/unit-test/unit-test.md`一样的测试规范，两者的区别在于待测对象。我们将测试空间较大需要迭代测试的模块，以及需要一步步集成的模块组的测试，作为ci-test的DUT。
通常情况下，将多个`test/hw/unit-test/`下的ip和submodules按照简单的guidance中的标准拓扑集成，即可得到一个ci-test。

## 测试框架


