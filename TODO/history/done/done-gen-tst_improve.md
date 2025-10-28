# done-gen-tst_improve

## Step 0: 初始化
- status: completed
- duration: 00m
- tokens: ~0
- notes: 创建装饰后的 todo，并准备执行计划

## Step 1: 梳理现有测试驱动与校验模式
- status: completed
- duration: 12m
- tokens: ~1100
- notes: 归纳出四类测试：FSM 依赖内部 RegArray 与状态跳转；RegFile 需要多信号协同驱动与时序参考模型；Adder 属于一次性组合逻辑激励；Decoder 使用外部资源并解析富文本日志。总结了 driver 样板中重复的计数器/Case 序列模式，以及 check(raw) 中常见的日志解析 + 参考模型比对流程。

## Step 2: 起草 stimulus/validator 接口草案
- status: completed
- duration: 35m
- tokens: ~2100
- notes: 在 `docs/testing/stimulus_validator_template.md` 中描述了 StimulusTimeline/StimulusDriver 抽象、LogChecker 组件及针对四类模块的适配策略，并列出后续实现清单。

## Step 3: 实现通用 stimulus 构建工具
- status: completed
- duration: 165m
- tokens: ~7600
- notes: 新增 `assassyn/python/assassyn/test/stimulus.py` 并导出接口；`test/hw/unit-test/ip/test_adder.py`、`test/hw/unit-test/ip/test_regfile.py`、`test/hw/unit-test/ip/test_alu.py` 迁移至 StimulusTimeline（含多端口、多类型 case_map）；`test/hw/unit-test/guide` 中的 `bypass/pipe/stall/branch/fsm` 驱动同步使用 StimulusTimeline 驱动或取值，分别通过离线运行验证。

## Step 4: 统一 check(raw) 验证接口
- status: completed
- duration: 150m
- tokens: ~7200
- notes: 实现 `assassyn/python/assassyn/test/checker.py`（Prefix/RegexExtractor、KeyValueParser、LogChecker、ReferenceHook 等），在 `__init__.py` 导出；`test/hw/unit-test/ip/test_adder.py`、`test/hw/unit-test/ip/test_alu.py`、`test/hw/unit-test/ip/test_regfile.py`、`test/sw/test_decoder.py`、`test/hw/unit-test/guide/bypass.py`、`pipe.py`、`stall.py`、`branch.py` 的 `check` 逻辑迁移至新接口（含参考模型、跨周期关系、日志统计），对应测试离线运行通过。

## Step 5: 示例整合与改造建议
- status: completed
- duration: 38m
- tokens: ~1800
- notes: 在 `docs/testing/stimulus_validator_template.md` 补充 Stimulus/LogChecker 代码片段及迁移清单，梳理 adder/regfile/decoder/guide 样例的差异化要点，并总结迁移步骤供后续测试套件参考。
