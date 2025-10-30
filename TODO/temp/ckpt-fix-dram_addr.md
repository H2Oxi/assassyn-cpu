# ckpt-fix-dram_addr

## ckpt-1: Executor dcache offset 支持

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 修改内容
- 为 `Executor.build()` 新增 `addr_offset` 参数并在 docstring 中记录用途，默认值保持 0 兼容旧调用
- 在 dcache 地址模块引入 `offset_adjust = UInt(32)((-addr_offset) % 2^32)`，通过加法完成物理地址到缓存索引的平移
- 保留原始 `adder_result` 喂给 MemoryAccessor、跳转预测等路径，仅对 `mem_addr` 使用平移后的结果
- 添加注释说明 offset 处理流程，提醒维护者这是 SRAM 视角的地址转换

### 验证要点
- 检查 elaboration 生成的地址逻辑是否仍产出 `UInt(depth_log)`，无类型回归
- 对 `addr_offset=0`、`addr_offset=0xb8`、`addr_offset=-0x10094` 等常见值进行手工推导，确认补码加法得到期望结果
- 关注 offset 调整是否会影响日志输出或下游的写回/跳转值（本次未改动这些信号）

### 当前状态
🚧 等待用户确认，可在确认后继续 Step 3

---

## ckpt-2: 顶层构建传递 dcache offset

### 修改文件
- `impl/gen_cpu/main.py`

### 修改内容
- `top()` 函数新增 `dcache_addr_offset` 参数（默认 0），并在文档注释中解释其作用
- 调用 `executor.build()` 时传递 `addr_offset=dcache_addr_offset`，保持原有调用顺序，兼容历史调用者
- 保持 `top()` 的返回接口不变，为新旧测试脚本提供统一入口

### 验证要点
- 现有调用（若未传参）能否继续成功构建 CPU
- 为测试脚本单独设置 offset 时，是否能够正确传递到 Executor

### 当前状态
🚧 等待用户确认，确认后继续 Step 4

---

## ckpt-3: 测试流程应用 data_offset

### 修改文件
- `test/sw/test_base.py`

### 修改内容
- `init_workspace()` 新增对 `.config` 文件的复制，确保测试工作目录具备 workload 配置
- 添加 `_load_workload_config()`，通过 `ast.literal_eval` 解析配置字典（支持十六进制字面量）
- `build_cpu()` 调用中读取 `data_offset` 并通过 `addr_offset` 传递给 `executor.build()`

### 验证要点
- 0to100 工作负载应获得 `data_offset = 0xb8`，从而修正 dcache 实际访问地址
- 无配置文件的场景默认 offset=0，保持对其他测试的兼容
- 配置解析失败时抛出异常，避免静默使用错误 offset

### 当前状态
🚧 等待用户确认，确认后继续 Step 5
