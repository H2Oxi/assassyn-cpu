# todo-fix-base_test

oct,27,21:10,tbd

**任务类型**: fix

## 目标

修复 `test/sw/test_base.py`，使其能够正确运行并验证CPU实现。

## Step 1: 在 test/sw/test_base.py 中设计 driver 并设置启动条件

参考 `test/sw/test_decoder.py` 中的 Driver 实现：
- 创建一个 Driver module，使用计数器生成地址
- 从 SRAM 中读取指令
- 设置启动条件：当 cnt[0] > 10 时才开始 async call fetchor
- 让整个CPU开始运行

**ckpt-1**: 验证 Driver 实现正确，能够控制CPU的启动时机

## Step 2: 在 impl 中加入 log

需要在以下位置添加日志输出：
1. **Fetchor**: 对 fetch address 进行 log
2. **Decoder**: 对读到的 instruction data 进行 log
3. **WriteBack**: 对每次要写的 rd 和 rd_data 进行 log

日志格式应与 `test/sw/test_decoder.py` 中的格式类似，使用 `log()` 函数。

**ckpt-2**: 验证各阶段的log输出正确，能够追踪CPU执行流程

## Step 3: 参考 0to100.sh 设计匹配的验证脚本

查看 `resources/riscv/benchmarks/0to100.sh` 的验证逻辑：
- 该脚本使用 writeback 的 log 进行验证
- 提取 x14 寄存器的累加和
- 提取 x10 寄存器的最终值
- 与 .data 文件中的参考值比较

需要修改 `test/sw/test_base.py` 中的 `check()` 函数：
- 确保验证逻辑能够正确匹配新的日志格式
- 或确认现有的验证逻辑已经兼容

**ckpt-3**: 验证脚本能够正确解析log并进行验证

## Step 4: 运行验证（初步）

运行完整的测试：
```bash
python test/sw/test_base.py
```

确保测试通过，CPU能够正确执行 0to100 workload。

**ckpt-4**: ⚠️ 发现 CPU 缺少跳转逻辑，需要继续修复

## Step 5: 实现跳转控制逻辑

根据 Step 4 的发现，CPU 缺少跳转逻辑支持。需要实现完整的控制流。

### 背景分析

从 `impl/external_src/ins_decoder.sv` 分析得知，所有跳转指令的目标地址都可以在 Executor 阶段通过 Adder 计算完成：

1. **Branch 指令（BEQ, BNE, BLT, BGE, BLTU, BGEU）**:
   - 目标地址: `PC + imm_b` (通过 Adder 计算)
   - 条件判断: 使用 `cmp_out` (ALU 比较器输出)
   - 控制信号: `addr_purpose = ADDR_BR`, `cmp_out_used = 1`

2. **JAL 指令**:
   - 目标地址: `PC + imm_j` (通过 Adder 计算)
   - 无条件跳转
   - 控制信号: `addr_purpose = ADDR_BR`

3. **JALR 指令**:
   - 目标地址: `(RS1 + imm_i) & ~1` (通过 Adder + 后处理)
   - 无条件跳转
   - 控制信号: `addr_purpose = ADDR_IND`, `add_postproc = 1`

### Step 5.1: 创建 jump_predictor_wrapper Downstream 模块

在 `impl/gen_cpu/downstreams.py` 中创建新的 downstream 模块：

```python
class jump_predictor_wrapper(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, ...):
        # 管理跳转控制逻辑
        pass
```

该模块的职责：
1. 接收跳转信号 + 跳转目标地址（来自 Executor 的 `adder_result`）
2. 接收跳转条件（来自 Executor 的 `cmp_out`）
3. 判断是否真正需要跳转
4. 管理 PC 更新逻辑（PC+4 vs 跳转目标）
5. 提供更新后的 PC 给 Fetchor

**ckpt-5.1**: jump_predictor_wrapper 模块创建完成

### Step 5.2: 在 Decoder 中添加跳转检测和 valid 控制

修改 `impl/gen_cpu/pipestage.py` 中的 Decoder：

1. **检测跳转指令**: 从 decoder 输出中识别 `addr_purpose` 是否为跳转相关（ADDR_BR, ADDR_IND, ADDR_J）
2. **管理 valid 控制**:
   - 创建 RegArray 变量来控制 valid 信号
   - 当检测到跳转指令时，将 valid 置为无效
   - 等待 jump_predictor_wrapper 返回地址更新完成信号
   - 地址更新生效后的下一个 cycle，恢复 valid

目的：确保跳转指令只被处理一次，避免在 PC 更新前重复译码。

**ckpt-5.2**: Decoder 的 valid 控制逻辑实现完成

### Step 5.3: 修改 Executor 传递跳转信息

修改 `impl/gen_cpu/pipestage.py` 中的 Executor：

1. 将 `adder_result` (跳转目标地址) 传递给 jump_predictor_wrapper
2. 将 `cmp_out` (branch 条件) 传递给 jump_predictor_wrapper
3. 将 `addr_purpose` 传递给 jump_predictor_wrapper（判断跳转类型）

**ckpt-5.3**: Executor 传递跳转信息完成

### Step 5.4: 修改 Fetchor 接收 PC 更新

修改 `impl/gen_cpu/pipestage.py` 中的 Fetchor：

1. 接收 jump_predictor_wrapper 提供的 PC 值作为输入
2. 修改 PC 更新逻辑：
   - 原来：`pc_reg[0] <= pc_reg[0] + 4`
   - 修改后：使用 jump_predictor_wrapper 提供的值

**ckpt-5.4**: Fetchor 的 PC 更新逻辑修改完成

### Step 5.5: 在 test_base.py 中连接 jump_predictor_wrapper

修改 `test/sw/test_base.py` 的 build_cpu 函数：

1. 实例化 jump_predictor_wrapper
2. 在正确的位置 build 它
3. 连接所有必要的信号

**ckpt-5.5**: jump_predictor_wrapper 在测试中正确连接

### Step 5.6: 运行验证（最终）

再次运行测试：
```bash
python test/sw/test_base.py
```

验证：
- CPU 能够正确执行跳转指令
- 循环能够正常工作
- 0to100 测试通过
- 验证脚本输出正确

**ckpt-5.6**: 测试通过，CPU 跳转逻辑工作正常
