# Stimulus & Validator Template

## 背景与目标

1. **降低 Driver 样板代码复杂度**  
   目前的大部分单元测试都需要手写 `RegArray` 计数器、`case` 表以及多路 `async_called` 调用。不同模块类型（组合逻辑、时序模块、FSM）在驱动方式上高度相似，但每次都要重新编写同样的控制流与常量定义。

2. **统一 `check(raw)` 验证接口**  
   `check_raw` 函数普遍包含以下重复结构：日志行过滤 → 解析字段 → 参考模型对比 → 报错/统计输出。随着模块类型增加，手写解析逻辑的重复度也越来越高，需要一个可重用的框架。

## 现有模式总结

| 场景 | 驱动模式 | 日志/验证模式 | 特殊需求 |
| --- | --- | --- | --- |
| `guide/fsm.py` | 计数器 + 条件调用，下游 FSM 内部状态维持 | 仅检查 `raw is not None` | 调试用途，需支持状态打印 |
| `ip/test_regfile.py` | 多信号同时驱动，Case 表描述时序，依赖参考模型模拟延迟 | 解析 `[test]` 前缀日志，基于 `RefRegFile.tick()` 逐周期对比 | 需要跟踪状态寄存器，输出数量多 |
| `ip/test_adder.py` | 计数器驱动两个输入，组合逻辑 | 解析三段式日志，直接调用 `ref_model` | 需要自动统计激励次数 |
| `sw/test_decoder.py` | SRAM + 外部资源，异步调用 | 解析富文本日志，统计错误条目 | 需要灵活的日志格式匹配与字段映射 |

总的来看，driver 的重复点集中在：
- `RegArray` 计数器 + `case` 语句 + 默认值驱动
- 多个下游端口需要同步调用
- 随机 / 顺序 / 定制 pattern 差异化不大

checker 的重复点集中在：
- 过滤带前缀的日志行
- 解析 `key:value` 或 `a:b|c:d` 类格式
- 将行转换为结构化数据，再与参考模型比对
- 统计通过/失败数量，生成断言

## 通用 Stimulus 模板设计

### 抽象概念

| 抽象 | 说明 |
| --- | --- |
| `StimulusTimeline` | 维护周期编号到事件的映射，支持区间/列表/默认模式 |
| `StimulusSignal` | 针对某个端口定义数据生成方式，可引用 Python callable 或固定表 |
| `StimulusDriver` | 结合 `RegArray` 计数器，在 `Module.build` 中产出目标端口并执行 `async_called` |

### API 草案

```python
from typing import Callable, Mapping, Sequence, Union
from assassyn.frontend import RegArray, UInt, Module, module

class StimulusTimeline:
    def __init__(self, counter_width: int = 32):
        self.counter_width = counter_width
        self._events = []

    def on(self, cycle: Union[int, range, Sequence[int]], action: Callable[[int], dict]):
        """注册在指定周期执行的回调，返回 dict 用于 async_called 的 kwargs"""

    def default(self, action: Callable[[int], dict]):
        """设置未匹配周期的默认行为"""

    def build_counter(self, typ=UInt) -> RegArray:
        """在 driver 中创建计数器 RegArray"""

    def emit(self, counter):
        """根据 counter 当前值调用注册的 action"""

class StimulusDriver:
    def __init__(self, timeline: StimulusTimeline):
        self.timeline = timeline

    def drive(self, *targets):
        """
        targets: List[Callable[[dict], None]] 例如 lambda payload: forward.async_called(**payload)
        支持对多个模块进行广播
        """
```

在 Driver 中的使用示例（伪代码）：

```python
from assassyn.frontend import Int, Module, UInt, module
from assassyn.test import StimulusDriver, StimulusTimeline

timeline = StimulusTimeline()
timeline.on({0: {...}, 1: {...}, 10: {...}}, lambda cycle: {...})
timeline.default(lambda cycle: {"data": UInt(5)(0)})

stim_driver = StimulusDriver(timeline)

class Driver(Module):
    @module.combinational
    def build(self, forward_rs1: Module, forward_rs2: Module):
        cnt = stim_driver.timeline.build_counter()
        payload = stim_driver.timeline.emit(cnt[0])
        stim_driver.drive(
            lambda data: forward_rs1.async_called(data=data["rs1"]),
            lambda data: forward_rs2.async_called(data=data["rs2"]),
        )
```

额外特性：
- `StimulusSignal.case(mapping, default)` 提供更接近当前 `case` 语法的封装
- 支持 `repeat(sequence, every=n)`、`ramp(start, step)` 等常见模式
- 提供 `log_each(logger, fmt, **fields)` 便于输出统一格式日志

## 通用 `check(raw)` 接口设计

### 抽象概念

| 抽象 | 说明 |
| --- | --- |
| `LogExtractor` | 负责过滤日志行，支持前缀、正则或自定义函数 |
| `LogParser` | 将日志行转换为结构化 dict，内置常见分隔符解析器 |
| `ReferenceModel` | Python callable，每次接受解析后的记录并返回期望结果 |
| `AssertionSuite` | 包含一组断言规则（精确匹配、范围、计数等），统一输出信息 |

### API 草案

```python
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

@dataclass
class LogRecord:
    cycle: int
    payload: dict

class LogChecker:
    def __init__(self, extractor, parser):
        self.extractor = extractor
        self.parser = parser
        self._hooks = []
        self._summary = {}

    def expect(self, name: str, func: Callable[[LogRecord], None]):
        """注册检查 hook，可以在 func 内部断言或调用 reference model"""

    def collect(self, raw: str):
        for line in self.extractor(raw.splitlines()):
            record = self.parser(line)
            for hook in self._hooks:
                hook(record)

    def summary(self):
        return self._summary
```

预置策略：
- `PrefixExtractor("[test]")` 用于简单前缀过滤
- `KeyValueParser(sep='|', kv_sep=':')` 针对 `key:value|key:value` 格式
- `RegexParser` 以命名分组捕获复杂日志
- `ReferenceHook(model, compare=lambda rec, ref: ...)` 封装参照模型对比

### 模块类型映射

| 模块类型 | 提供的辅助能力 |
| --- | --- |
| FSM | 自动追踪状态变化，支持 `watch_state("s3")` |
| 时序外设 | 缓存历史记录，提供 `with_history(n)` 接口用于延迟比对 |
| 组合逻辑 | 内置 `count_expect(total)` 验证运行次数 |
| 复杂日志 | 支持多前缀、多 parser，支持错误聚合输出 |

## 示例路线

1. **RegFile**  
   - Stimulus: 使用 `StimulusTimeline.case_map()` 一次性定义 `rs1_addr`/`rs2_addr`/`rd_we` 等信号  
   - Checker: 使用 `KeyValueParser` 解析 `[test]` 行，挂载 `ReferenceHook(RefRegFile.tick)`

2. **Adder**  
   - Stimulus: 使用 `StimulusSignal.sequence()` 生成输入对  
   - Checker: 使用 `count_expect(99)` + `ReferenceHook(ref_model)`

3. **Decoder**  
   - Stimulus: 提供 `SRAMStimulus` 帮助加载文件并驱动  
   - Checker: 使用 `RegexParser` + `AggregationRule` 统计错误数量

## 使用示例

### Stimulus 快速上手

以下片段摘自 `test/hw/unit-test/ip/test_adder.py`，演示如何用 `StimulusTimeline` 和 `StimulusDriver` 驱动多个端口：

```python
timeline = StimulusTimeline()

def _signed(value: int):
    return lambda _: Int(32)(value).bitcast(UInt(32))

timeline.signal("add_in1", UInt(32)).sequence([_signed(-100), _signed(0), _signed(100)]).default(lambda cnt: cnt)
timeline.signal("add_in2", UInt(32)).sequence([_signed(100), _signed(-100), _signed(-1)]).default(lambda cnt: cnt)

class Driver(Module):
    @module.combinational
    def build(self, forward1: Module, forward2: Module):
        counter = timeline.build_counter()
        counter[0] = counter[0] + timeline.counter_dtype(timeline.step)

        stim = StimulusDriver(timeline)
        stim.bind(forward1.async_called, data="add_in1")
        stim.bind(forward2.async_called, data="add_in2")
        stim.drive(counter[0])
```

常见模式：
- `timeline.signal(...).case_map({...}, default=...)` 用于离散周期控制（`test_regfile.py`）。
- `sequence([...], start=n)` 适合短序列后再衔接默认值。
- 通过 `StimulusDriver.bind` 绑定多个 `async_called` 目标，构建广播式驱动。

### 日志校验与参考模型

`LogChecker` 可以组合多种 extractor / parser，并用 hook 连接参考模型：

```python
checker = LogChecker(
    PrefixExtractor("[test]", mode="contains"),
    KeyValueParser(pair_sep="|", kv_sep=":"),
)

checker.expect_count(99)  # 或 expect_at_least(...)

checker.add_hook(
    ReferenceHook(
        ref_model,
        inputs=["add_in1", "add_in2"],
        outputs=["add_out"],
        name="adder_ref",
    )
)

checker.collect(raw)
```

在 `test_regfile.py` 中，还演示了：
- 自定义 hook 维护跨周期状态并打印前若干周期的调试信息。
- 使用 `checker.summary["count"]` 反馈成功记录数量。

## Sample 测试迁移指南

- `test/hw/unit-test/ip/test_adder.py`: 使用 `StimulusTimeline.sequence` + `default` 生成加法器输入；`ReferenceHook` 直接对比参考模型。适合作为组合逻辑迁移模板。
- `test/hw/unit-test/ip/test_regfile.py`: 通过 `case_map` 管理多端口时序，示范如何在 hook 内维护延迟模型与调试输出。
- `test/sw/test_decoder.py`: 结合 `RegexExtractor`/`RegexParser` 解析富文本日志，展示自定义字段映射与聚合。
- `test/hw/unit-test/guide/*.py`: 基础教学样例已集成 `StimulusTimeline`。迁移其他老驱动时，可对照这些文件逐项替换 `RegArray`/`case`/`async_called` 模式。

迁移现有测试时建议遵循：
1. 先梳理原 driver 中的周期事件，逐项映射为 `StimulusTimeline.signal(...).case_map/sequence`。
2. 检查日志格式，选择合适的 `Extractor`/`Parser` 组合，必要时编写简单 wrapper。
3. 将参考模型或断言逻辑封装为 hook，复用 `ReferenceHook` 或自定义函数，使用 `require` 明确字段依赖。
4. 在完成迁移后，通过 `expect_count`/`summary` 记录覆盖情况，并补充调试输出以便初次验证。
