# todo-add-bypass

oct,29,15:50,tbd

**任务类型**: fix

## 目标

为 Executor → MemoryAccessor 的流水段引入 rd/rd_data 旁路寄存器，并在 Executor 阶段对 rs1/rs2 进行 MA→EX 旁路选择，确保依赖上一条指令结果的指令无需等待写回即可取到最新数据。

## Step 1: 在 impl/gen_cpu/main.py 中引入 MA 阶段寄存器

- 在 `top()` 内创建用于 MA→WB 的 rd、rd_data、wb_en 寄存器
- 将寄存器传递给 Executor 和 MemoryAccessor，以便共享阶段间数据
- 调整 `memory_accessor.build(...)` 的调用参数顺序和含义

**ckpt-1**: 首次修改 `impl/gen_cpu/main.py` 后记录寄存器接入结果

## Step 2: 更新 Executor / MemoryAccessor 的流水接口并实现旁路

- 扩展 `Executor` 端口以接收 rs1/rs2 地址，并读取 MA 阶段寄存器
- 在 `Executor.build` 中加入 MA→EX 旁路选择，覆盖 ALU/Adder/mem 写数据路径
- 在 `MemoryAccessor.build` 中写入 MA 寄存器，同时维持原有 write_back 接口

**ckpt-2**: 首次修改 `impl/gen_cpu/pipestage.py` 后验证旁路逻辑结构

## Step 3: 同步外部构建逻辑

- 更新 `test/sw/test_base.py` 等调用点以传递新增的寄存器参数
- 确认测试构建流程仍然能够实例化并连线各阶段

**ckpt-3**: 首次修改 `test/sw/test_base.py` 后确认接口匹配

## Step 4: 完善 MA→EX 旁路寄存器写入路径

- 让 `MemoryAccessor` 以寄存器形式接收 `rd`/`rd_data`/`wb_en`，消除对旧 port 形态的依赖
- 为 load 指令补齐旁路寄存器写入流程，使下一拍 Executor 能读取到最新的内存数据
- 调整 `Executor` 的旁路控制，仅依赖寄存器状态判定 RAW 冒险

**ckpt-4**: 更新 `impl/gen_cpu/pipestage.py` 后确认 load-use 场景的旁路数据来源

## Step 5: 运行验证并整理日志

- 执行 `python test/sw/test_base.py`，确认 0to100 基准测试通过
- 检查 `raw.log` 旁路相关日志，确保无回归
- 若通过，准备整理 history；若失败，记录问题等待反馈
