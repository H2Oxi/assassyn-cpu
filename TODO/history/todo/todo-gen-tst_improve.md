# todo-gen-tst_improve

oct,29,10:00,tbd

**任务类型**: dev

## 目标

- 设计一个通用的 stimulus 生成模版，降低每个 driver 的样板代码复杂度
- 规划一个统一的 `check(raw)` 验证接口，使不同模块类型能够使用一致的抓取逻辑

## Step 1: 梳理现有测试驱动与校验模式

- 阅读 `test/hw/unit-test/guide/fsm.py`, `test/hw/unit-test/ip/test_regfile.py`, `test/hw/unit-test/ip/test_adder.py`, `test/sw/test_decoder.py`
- 记录 stimulus 编排、日志格式、参照模型等共性与差异

## Step 2: 起草 stimulus/validator 接口草案

- 在 `docs/testing/stimulus_validator_template.md` 中总结抽象需求与接口草图
- 列出需要覆盖的模块类型以及参数化要点

**ckpt-1**: 文档初稿完成，等待用户确认是否按此方向实现

## Step 3: 实现通用 stimulus 构建工具

- 在 `assassyn/python/assassyn/test/stimulus.py` 中实现基础 Builder/Sequencer
- 支持组合逻辑、时序逻辑、FSM 等场景的输入驱动
- 在 `test/hw/unit-test/ip/test_adder.py`、`test/hw/unit-test/ip/test_regfile.py` 中替换 driver，实现多类型示例验证

**ckpt-2**: 基础工具实现完成，提交接口说明与示例
**ckpt-3**: 组合逻辑测试（adder）迁移至新 Stimulus 验证通过
**ckpt-3b**: 时序模块测试（regfile）迁移至新 Stimulus 验证通过

## Step 4: 统一 check(raw) 验证接口

- 在 `assassyn/python/assassyn/test/checker.py` 中实现日志抓取、reference hook、断言工具
- 在 `assassyn/python/assassyn/test/__init__.py` 中导出新接口，并在 adder/regfile/decoder 测试中落地

**ckpt-4**: 验证接口实现完毕，并在多种测试场景中验证 API

## Step 5: 示例整合与改造建议

- 在 `docs/testing/stimulus_validator_template.md` 中补充使用示例
- 为 sample 测试编写迁移指南，并在 done 文件中记录后续建议
