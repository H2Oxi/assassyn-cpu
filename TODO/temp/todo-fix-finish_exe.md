# todo-fix-finish_exe

oct,29,13:00,tbd

**任务类型**: fix

## 目标

为 CPU pipeline 增加 finish() 触发条件：当执行 ebreak/ebreak/halt/ecall 或在 executor 发现无限自跳转时结束仿真。

## Step 0: 阅读现有实现与参考资料

- 梳理 `impl/gen_cpu/pipestage.py` 中 decoder、executor 的当前逻辑
- 查阅 `docs/assassyn_lan.md`，确认 finish 调用约定

## Step 1: Decoder 识别终止指令并标记 executor

- 找到 decoder 推送任务给 executor 的数据结构
- 为 ebreak/halt/ecall 等指令增加标志位，让 executor 能检测到
- 若尚无合适字段，则在传输结构中补充

**ckpt-pipestage**: 首次修改 `impl/gen_cpu/pipestage.py` 完成后创建 checkpoint，记录 decoder 改动

## Step 2: Executor 触发 finish()

- 在 executor 读取 decoder 标记：识别 ebreak/halt/ecall 并调用 finish()
- 添加检测逻辑：若跳转目标等于当前 PC，视为死循环并调用 finish()
- 确保 finish 仅触发一次且不影响其它指令执行

## Step 3: 基本验证

- 运行现有最小化或样例程序（若有）观察 finish 是否触发
- 若缺少自动测试，至少执行 `python test/sw/test_base.py` 并关注尾部日志
- 记录输出重点（遵循调试日志截取规则）

## Step 4: 收尾

- 整理修改摘要，确认无遗漏
- 等待用户确认是否归档 todo/done
