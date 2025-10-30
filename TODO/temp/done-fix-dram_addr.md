# done-fix-dram_addr

oct,29,17:20,tbd

## Step 0: 创建修饰后的 todo 文件

**Status**: ✅ Completed  
**Time**: ~6 min  
**Tokens**: ~1500

### 完成内容
- 阅读 `TODO/decorator-rules.md` 并确认 ckpt/todo 流程
- 拆解原始任务，生成 `TODO/temp/todo-fix-dram_addr.md`
- 规划需要触及的模块（pipestage、main、test_base）

## Step 1: 梳理现有的数据地址流程

**Status**: ✅ Completed  
**Time**: ~9 min  
**Tokens**: ~2200

### 完成内容
- 通读 `impl/gen_cpu/pipestage.py`，定位 `dcache` 地址生成逻辑
- 查看 `impl/gen_cpu/main.py` 与 `test/sw/test_base.py` 的构建顺序及 `executor.build()` 调用方式
- 检查 `resources/riscv/benchmarks/0to100.config`，确认 `data_offset`=0xb8 并调研其他用例可能存在的负 offset

## Step 2: 在 Executor 中加入地址 offset 支持

**Status**: ✅ Completed  
**Time**: ~14 min  
**Tokens**: ~2600

### 完成内容
- 为 `Executor.build()` 增加 `addr_offset` 参数，扩展文档说明其用途
- 使用二进制补码形式引入 `offset_adjust` 常量，实现 `adder_result` 到 dcache 视图的地址平移
- 保留原始 `adder_result` 供跳转、写回等后续逻辑使用，仅在计算 `mem_addr` 时应用 offset
- 添加注释说明地址转换流程，避免后续维护混淆

### 修改的文件
- impl/gen_cpu/pipestage.py

### 验证状态
**ckpt-1**: ⏳ 等待用户确认（确认 offset 逻辑与类型处理符合预期）

## Step 3: 在 top 构建流程传递 offset

**Status**: ✅ Completed  
**Time**: ~11 min  
**Tokens**: ~1800

### 完成内容
- 为 `impl/gen_cpu/main.py.top()` 新增 `dcache_addr_offset` 参数（默认 0），更新注释说明其含义
- 在调用 `executor.build()` 时传递 `addr_offset=dcache_addr_offset`，保持其余参数顺序不变
- 检查文件其他引用，确认默认参数可兼容现有调用者

### 修改的文件
- impl/gen_cpu/main.py

### 验证状态
**ckpt-2**: ⏳ 等待用户确认（确认顶层构建出口参数设计合理）

## Step 4: 在基准测试中配置 0xb8 offset

**Status**: ✅ Completed  
**Time**: ~12 min  
**Tokens**: ~2100

### 完成内容
- 在 `init_workspace()` 中复制 `.config` 文件到工作目录，便于测试读取 workload 配置
- 新增 `_load_workload_config()` 解析配置文件（使用 `ast.literal_eval` 支持十六进制常量）
- 在 `build_cpu()` 中读取 `data_offset`，并通过 `addr_offset` 参数传递给 `executor.build()`
- 对 0to100 workload 自动套用 `data_offset = 0xb8`，其他没有配置的场景默认 0

### 修改的文件
- test/sw/test_base.py

### 验证状态
**ckpt-3**: ⏳ 等待用户确认（确认测试中 0xb8 offset 传递逻辑正确）

## Step 5: 验证行为

**Status**: ⚠️ Blocked  
**Time**: ~18 min  
**Tokens**: ~5200

### 执行内容
- 通过 `python test/sw/test_base.py` 重新构建/运行仿真，确认 offset 生效后的整体行为
- 按要求仅提取 `raw.log` 末尾 50/200 行分析访存/写回轨迹
- 计算 `writeback` 日志中 x14/x10 的聚合值验证与参考数据的差异

### 发现问题
- 测试失败：`AssertionError: x10 final value mismatch ... got 0x97a2d, expected 0x99f89`
- `writeback x14` 的累加和与参考值 0x99f89 相符，但 `x10` 最终未包含首个数据 0x255c
- 观察日志发现首轮 `add x10, x10, x14` 时，x10 仍为 0，推测为 load→use 冒险导致缺少首个加数
- 该行为与 dram offset 改动无直接因果，但会阻止本 todo 的最终验证通过

### 后续建议
- 等待用户确认是否在本任务继续处理 load-use hazard，或另开 todo
