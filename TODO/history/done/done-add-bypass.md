# done-add-bypass

oct,29,15:50,tbd

## Step 0: 创建修饰后的 todo 文件

**Status**: ✅ Completed
**Time**: ~6 min
**Tokens**: ~4500

### 完成内容
- 阅读 `TODO/decorator-rules.md`，明确 step/ckpt 要求
- 拆解 `TODO/todo-add-bypass.md` 并生成 `TODO/temp/todo-add-bypass.md`
- 建立后续记录文件 `TODO/temp/done-add-bypass.md`

## Step 1: 在 impl/gen_cpu/main.py 中引入 MA 阶段寄存器

**Status**: ✅ Completed
**Time**: ~7 min
**Tokens**: ~3200

### 完成内容
- 在 `impl/gen_cpu/main.py:70` 附近创建 `ma_stage_rd`、`ma_stage_rd_data`、`ma_stage_wb_en` 三个 RegArray（UInt(5)/UInt(32)/Bits(1)）
- 将寄存器引用传递给 `executor.build(...)` 与 `memory_accessor.build(...)` 以便后续阶段共享
- 保持原有 regfile_wrapper 连接不变，仅补充流水寄存器

### 创建的文档
- `TODO/temp/ckpt-add-bypass.md`（记录 ckpt-1）

### 后续
- Step 2 中更新 `impl/gen_cpu/pipestage.py` 以实际读写这些寄存器并实现旁路

## Step 2: 更新 Executor / MemoryAccessor 的流水接口并实现旁路

**Status**: ✅ Completed
**Time**: ~20 min
**Tokens**: ~6400

### 完成内容
- 扩展 `Executor` 端口列表，新增 `rs1_addr`/`rs2_addr`，并在 build 参数中要求传入 MA 寄存器
- 在 `Executor.build` 中实现 MA→EX 旁路逻辑，统一用于 ALU、Adder、存储写数及调试日志
- 更新 `MemoryAccessor.build` 接口以写入寄存器，同时保持对 WriteBack 的 async 调用
- 调整 `Decoder.build` 调用，补充传递源寄存器地址；通过 `python -m compileall impl/gen_cpu/pipestage.py` 验证语法

### 相关文档
- `TODO/temp/ckpt-add-bypass.md` 新增 ckpt-2 记录

### 后续
- Step 3 更新测试构建脚本以传入新增参数，确保运行路径一致

## Step 3: 同步外部构建逻辑

**Status**: ✅ Completed
**Time**: ~6 min
**Tokens**: ~2100

### 完成内容
- 在 `test/sw/test_base.py` 中创建与主实现一致的 MA 寄存器组
- 为 `executor.build` / `memory_accessor.build` 传入新增参数，保持构建顺序不变
- 更新 `TODO/temp/ckpt-add-bypass.md` 记录 ckpt-3

### 后续
- Step 4 完善 MA→EX 旁路寄存器写入路径后，再进入 Step 5 的运行验证阶段

## Step 4: 完善 MA→EX 旁路寄存器写入路径

**Status**: ✅ Completed
**Time**: ~18 min
**Tokens**: ~3600

### 完成内容
- 在 `impl/gen_cpu/pipestage.py` 中把 `dcache.dout` 作为 load/zero-extend load 的旁路数据源，确保 `ma_stage_rd_data` 在执行阶段就持有最新内存值。
- 取消对 load 的 bypass 禁止，让 `ma_stage_wb_en` 始终与 `wb_en` 保持一致，通过寄存器状态决定是否覆盖 RS1/RS2。
- 调整 `memory_accessor.async_called` 参数与 `MemoryAccessor.build`，现在 WriteBack 完全依赖共享寄存器拿到 `rd`/`rd_data`/`wb_en`，消除了对旧 port 的依赖。
- 在 `WriteBack.build` 内新增 `forward_*` 寄存器暴露写回信息，Executor 补充 WB→EX 旁路匹配，与 MA→EX 逻辑协同。
- 运行 `python -m compileall impl/gen_cpu/pipestage.py` 通过语法检查，并在 `TODO/temp/ckpt-add-bypass.md` 记录 ckpt-4。

### 后续
- Step 5 重新运行 `python test/sw/test_base.py` 验证 load-use 修复效果，并更新日志记录

## Step 5: 运行验证并整理日志

**Status**: ✅ Completed
**Time**: ~40 min
**Tokens**: ~6400

### 完成内容
- 引入 `ma_stage_load_*` 寄存器保持最新 load 数据有效，允许 Executor 在 load 后两拍仍可旁路该结果。
- 调整 MemoryAccessor 仅在 load 指令时更新 `ma_stage_load_valid` 而不清零，从而覆盖首轮 `lw -> add` RAW 冒险。
- 运行 `python test/sw/test_base.py`（末尾 50 行）验证通过，日志显示 `x10_final` 与参考值 `0x99f89` 一致。
- 检查 `raw.log` 初段，确认第一轮累加已包含 `0x255c`，旁路补丁生效。

### 命令记录
- `python -m compileall impl/gen_cpu/pipestage.py`
- `python test/sw/test_base.py`
