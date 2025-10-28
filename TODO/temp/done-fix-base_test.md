# done-fix-base_test

oct,27,21:10,tbd

## Step 0: 创建修饰后的 todo 文件

**Status**: ✅ Completed
**Time**: ~5 min
**Tokens**: ~6000

### 完成内容
- 读取并理解 decorator-rules
- 创建了修饰后的 todo 文件到 TODO/temp/todo-fix-base_test.md
- 分析了参考文件：test_decoder.py, test_base.py, 0to100.sh, pipestage.py
- 理解了整体架构和验证流程

## Step 1: 在 test/sw/test_base.py 中设计 driver 并设置启动条件

**Status**: ✅ Completed
**Time**: ~10 min
**Tokens**: ~9000

### 完成内容
- 修改了 test/sw/test_base.py 的导入语句
- 添加了 Driver 类（line 23-47）
- 重构了 build_cpu 函数（line 85-180）
- 使用 Driver 控制 Fetchor 的启动时机（cnt[0] > 10）

### 修改的文件
- test/sw/test_base.py

### 创建的文件
- TODO/temp/ckpt-fix-base_test.md

### 验证结果
**ckpt-1**: ✅ 用户确认通过

## Step 2: 在 impl 中加入 log

**Status**: ✅ Completed
**Time**: ~8 min
**Tokens**: ~3000

### 完成内容
- 在 Fetchor 中添加了 fetch address 的 log (pipestage.py:53-54)
- 在 Decoder 中添加了 instruction data 的 log (pipestage.py:85-86)
- 在 WriteBack 中添加了 rd 和 rd_data 的 log (pipestage.py:368-371)

### 日志格式
- `[fetchor] fetch_addr: 0x{:08x}` - 记录取指地址
- `[decoder] fetch_addr: 0x{:08x} ins: 0x{:08x}` - 记录指令地址和指令数据
- `[writeback] x{}: 0x{:08x}` - 记录寄存器写回（只在 wb_en=1 时）

### 修改的文件
- impl/gen_cpu/pipestage.py

### 验证结果
**ckpt-2**: ✅ 日志格式正确

## Step 3: 参考 0to100.sh 设计匹配的验证脚本

**Status**: ✅ Completed
**Time**: ~2 min
**Tokens**: ~500

### 完成内容
- 检查了 test_base.py 中的 check() 函数
- 确认现有实现已经支持 0to100.sh 验证
- init_workspace() 会复制 0to100.sh 到 workspace/workload.sh
- check() 会正确调用验证脚本并传递参数

### 结论
不需要额外修改，验证逻辑已完整。

## Step 4: 运行验证

**Status**: ⚠️ 部分完成（发现 CPU 实现缺陷）
**Time**: ~20 min
**Tokens**: ~4000

### 完成内容
1. 修复了路径问题（workload 文件路径）
2. 添加了 regfile_wrapper 的 optional 保护（参考 test_regfile.py）
3. 成功编译和运行 simulator
4. 日志输出正确

### 修改的文件
- test/sw/test_base.py (line 228: 修复 wl_path)
- impl/gen_cpu/downstreams.py (line 10-15: 添加 optional 保护)

### 发现的问题
**CPU 实现缺少跳转逻辑！**

验证失败：`Error Sum! 1912 != 630665`

根本原因：
- Fetchor 只是简单地每周期 PC+4
- 没有实现 branch/jal/jalr 的跳转逻辑
- 没有将跳转目标地址反馈给 Fetchor

详细分析见 ckpt-4。

### 验证结果
**ckpt-4**: ⚠️ 发现 CPU 缺少跳转逻辑

---

## 分析：跳转指令目标地址计算

**Status**: ✅ 完成
**Time**: ~10 min
**Tokens**: ~3500

### 分析结果

确认**所有跳转指令的目标地址都可以在 Executor 阶段通过 Adder 计算完成**：

1. **Branch 指令（BEQ, BNE, BLT, BGE, BLTU, BGEU）**:
   - 目标地址: `PC + imm_b`
   - 条件判断: `cmp_out`
   - Adder 配置: `add_in1=PC, add_in2=IMM`

2. **JAL 指令**:
   - 目标地址: `PC + imm_j`
   - 无条件跳转
   - Adder 配置: `add_in1=PC, add_in2=IMM`

3. **JALR 指令**:
   - 目标地址: `(RS1 + imm_i) & ~1`
   - 无条件跳转
   - Adder 配置: `add_in1=RS1, add_in2=IMM, add_postproc=CLR_LSB`

### 结论

Executor 已经计算了所有跳转目标地址（`adder_result`），只需要：
1. 将跳转信号和目标地址反馈给 Fetchor
2. 实现 PC 更新逻辑的选择（PC+4 vs 跳转目标）

---

## 更新 TODO：新增 Step 5 跳转控制逻辑

根据用户在原始 todo 中新增的第 5 条要求，以及我们的分析发现，已将 Step 5 添加到 `TODO/temp/todo-fix-base_test.md`：

**Step 5 包含 6 个子任务**：
- Step 5.1: 创建 jump_predictor_wrapper Downstream 模块
- Step 5.2: 在 Decoder 中添加跳转检测和 valid 控制
- Step 5.3: 修改 Executor 传递跳转信息
- Step 5.4: 修改 Fetchor 接收 PC 更新
- Step 5.5: 在 test_base.py 中连接 jump_predictor_wrapper
- Step 5.6: 运行最终验证

### 下一步
开始执行 **Step 5.1**: 创建 jump_predictor_wrapper Downstream 模块
