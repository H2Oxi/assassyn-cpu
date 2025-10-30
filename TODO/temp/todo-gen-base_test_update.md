# todo-gen-base_test_update

oct,29,15:07,tbd

**任务类型**: dev

## 目标
- 使用项目内的 `LogChecker` 校验 `test/sw/test_base.py` 的执行结果
- 摆脱外部 `0to100.sh`，实现 Python 内部的写回日志验证
- 当校验失败时输出包含时间戳的错误信息，便于定位问题

## Step 1: 梳理现有测试与日志
- 检查 `test/sw/test_base.py` 当前 driver / checker 结构
- 对比 `docs/testing/stimulus_validator_template.md` 与现有日志（写回寄存器格式）
- 明确需要支撑的校验指标（x14 累加值、x10 终值、参考数据来源）

## Step 2: 设计新的校验流程
- 规划 `LogChecker` + 解析器的组合，确定周期/寄存器/数值字段
- 设计错误报告格式，包含触发错误的周期（时间戳）与寄存器信息
- 评估是否需要扩展公共校验工具或可在测试内部完成

## Step 3: 替换 `check()` 实现并引入时间戳支持
- 读取 `raw.log` 和 `workspace/workload.data` 数据实现内部校验
- 使用 `LogChecker` 解析 `[writeback]` 日志并聚合 x14 / 记录 x10 终值
- 在断言失败时输出携带周期时间戳的详细信息

**ckpt-1**: test/sw/test_base.py 完成首次修改并梳理新的校验逻辑

## Step 4: 验证更新后的测试流程
- 运行 `python test/sw/test_base.py` 确认构建与仿真正常
- 检查 raw.log 与校验输出，确保无误报 / 漏报
- 根据结果更新必要的日志或提示信息

