# todo-fix-dram_addr

oct,29,17:20,tbd

**任务类型**: fix

## 目标

为 `Executor` 阶段提供可配置的数据内存地址 offset，使 `dcache` 访问基于物理地址减去 offset 的结果，确保 `test/sw/test_base.py` 在 `data_offset = 0xb8` 时能够正确命中数据缓存。

## Step 1: 梳理现有的数据地址流程

- 阅读 `impl/gen_cpu/pipestage.py` 中 `Executor.build()` 的内存地址生成逻辑
- 确认 `impl/gen_cpu/main.py` / `test/sw/test_base.py` 如何调用 `executor.build()`，并记录需要透传 offset 的位置
- 评估 offset 可能的默认值以及与 `resources/riscv/benchmarks/0to100.config` 的关系

## Step 2: 在 Executor 中加入地址 offset 支持

- 为 `Executor.build()` 增加 `addr_offset` 参数（默认 0），并在内部转换成 `UInt(32)` 参与计算
- 在计算 `dcache` 地址前执行 `adder_result - addr_offset`，确保结果再进行 index 截取时不会溢出
- 维护 `adder_result` 原值用于后续跳转/写回逻辑

**ckpt-1**: 首次修改 `impl/gen_cpu/pipestage.py`，确认 offset 减法与类型处理正确

## Step 3: 在 top 构建流程传递 offset

- 修改 `impl/gen_cpu/main.py` 的 `top()` 接口，加入 `dcache_addr_offset` 参数（默认 0）
- 调用 `executor.build()` 时传递该 offset，更新文档注释与调用说明

**ckpt-2**: 首次修改 `impl/gen_cpu/main.py`，确认新参数的默认值与调用一致

## Step 4: 在基准测试中配置 0xb8 offset

- 在 `test/sw/test_base.py` 的 CPU 构建流程中提供 `data_offset = 0xb8`
- 若存在共享配置文件（如 `.config`），确保读取逻辑覆盖 offset 设置并与新增接口匹配
- 检查可能需要传递 offset 的其他调用点（若无则记录原因）

**ckpt-3**: 首次修改 `test/sw/test_base.py`，确认测试使用 0xb8 offset

## Step 5: 验证行为

- 重新生成/构建必要的仿真工件
- 运行 `python test/sw/test_base.py`，核对 `raw.log` 中的访问日志是否消除了错误的地址偏移
- 如测试通过，整理可选的清理/文档更新建议

