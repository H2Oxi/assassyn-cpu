# assassyn language simple ref

## 概览

assassyn 语言围绕「端口队列 + 组合构建函数」的硬件建模接口展开。模块之间通过异步调用传递数据，内部主要依赖 `RegArray` 维护状态、`Value` 表达组合连线。本笔记整理常用构件的角色与约定，便于快速查阅。

## 模块

我们有大致三种模块。

### `module`

- 使用 `@module.combinational` 注册组合构建函数。
- `ports` 中的条目会被封装为 FIFO 输出，需要在 `build` 内通过 `self.pop_all_ports(True)` 或显式 `port.pop()` 取出。
- `build` 的形参只接受 `RegArray`，常用于在模块之间共享寄存器状态。
- 适合实现带强时序限制的数据流、驱动器或算术单元。

### `downstream`

- 组合函数通过 `@downstream.combinational` 声明。
- 入参可以直接使用 `Value`，因此常作为对齐/合并 Value 流的轻量级算子。
- 不存在端口队列，侧重并发组合操作。

### `ExternalSV`

- 用于挂接 SystemVerilog 等外部模块。
- `regout` 表示只读、带时序语义的 `RegArray`。
- `wireout` 和 `wirein` 都是 `Value`，方便与外部 IP 建立简单连线。
- 适用于复用现有 IP 或与测试基准进行互连。

## 调用约定

### `Port` 与 `pop_all_ports`

声明 `ports={'data': Port(UInt(32))}` 后，可在 `build` 起始处调用：

```python
payload = self.pop_all_ports(True)  # True 表示阻塞直到端口有效
```

这会按声明顺序返回一个容器，便于一次性拉取全部输入。

### `async_called`

模块之间的触发依赖 `async_called`：

```python
branch.async_called(data=values['data'])
```

被调用模块会在当拍内收到数据并执行自身 `build`。常与 `Condition` 结合，实现按需调度。

## 关键语法

### 变量类型

#### `RegArray`

- 使用 `RegArray(dtype, length, initializer=None)` 声明定长寄存器数组。
- 每个元素在同一组合周期内只允许一次赋值，是保存状态或跨模块共享寄存器的主要手段。

#### `Value`

- 即时变量，对应硬件中的 wire。
- 可以在同一组合块内多次重新赋值，最后一次写入生效。

#### `Array`

- 纯组合数组容器，常用于传递 valid/ready 等布尔向量。

### 赋值语句

#### `select`

`select` 提供链式条件赋值：在条件为真时返回候选值，否则回落到旧值。常用于替换 if-else，将多路选择器写成表达式。

```python
# Select ALU input 2: ZERO, RS2, or IMM
alu_in2 = UInt(32)(0)  # default ZERO
alu_in2 = (alu_in2_sel == UInt(2)(AluIn2Sel.RS2.value)).select(RS2_data[0], alu_in2)
alu_in2 = (alu_in2_sel == UInt(2)(AluIn2Sel.IMM.value)).select(imm, alu_in2)
```

#### `case`

`.case` 允许对寄存器值建立查找表，`None` 键充当默认分支。配合 `RegArray.case()` 可以在同一周期内根据状态选择不同常量或表达式。

```python
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
```

### 条件控制

#### `Condition`

`with Condition(expr):` 会在 `expr` 为真时执行上下文内语句，没有显式 `else` 时默认不做任何操作。典型用法可参考 `test/hw/unit-test/guide/branch.py`，在端口有效时才触发异步调用或写端口。

### 语法糖

#### `fsm`

`fsm.FSM` 帮助将状态转移表与状态体组合成寄存器驱动的有限状态机。示例见 `test/hw/unit-test/guide/fsm.py`：使用 `transfer_table` 描述跳转，`body_table` 填入在特定状态执行的组合逻辑。

### 结束控制

#### `finish`

`finish` 用于在仿真中显式结束模块行为或测试流。参考 `assassyn/python/ci-tests/test_finish.py` 了解其与测试框架的配合方式。
