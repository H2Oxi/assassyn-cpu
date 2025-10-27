# todo: CPU Implementation Update (gen)

oct,27,17:00,tbd

## 目标
根据设计的关键拓扑关系，实现缺失的还未完成的逻辑。每一段逻辑块的更新都视为ckpt，需要和用户确认正误。

## 文件说明
- `impl/gen_cpu/main.py`: driver，连接不同的模块
- `impl/gen_cpu/downstreams.py`: 流水线模块调用统一外部模块的枢纽(如regfile)或bypass相关包装
- `impl/gen_cpu/pipestage.py`: 流水线模块，asyncall连接通过fifo传给下一个模块

---

## Step 1: 实现Fetchor模块的完整逻辑

**任务描述**: Fetchor负责从icache获取指令

**实现要点**:
1. 接受driver的激励，初始化开始从头读instruction memory中的指令
2. 传递给decoder实际fetch的指令所对应的address

**涉及文件**: `impl/gen_cpu/pipestage.py`

**[CKPT-1]**: 验证Fetchor模块实现是否正确，包括:
- icache读取逻辑
- PC地址管理
- 与decoder的接口

---

## Step 2: 完善Decoder模块的数据传递

**任务描述**: Decoder译码指令为控制信号

**实现要点**:
1. i cache读出的指令作为regarray传递进来，输入给decoder译码
2. 把不同的decoder输出打包，作为return传递出去，方便在downstream使用

**涉及文件**: `impl/gen_cpu/pipestage.py`

**[CKPT-2]**: 验证Decoder模块是否正确:
- 指令译码输出完整性
- 与regfile_wrapper的接口连接
- 传递给executor的信号完整性

---

## Step 3: 实现Executor模块的完整逻辑

**任务描述**: Executor执行算术运算

**实现要点**:
1. 调用ALU进行算术/逻辑运算
2. 调用Adder进行地址计算
3. 设置data memory读取地址

**涉及文件**: `impl/gen_cpu/pipestage.py`

**[CKPT-3]**: 验证Executor模块:
- ALU输入选择逻辑(alu_in1_sel, alu_in2_sel)
- Adder输入选择逻辑
- memory地址设置逻辑
- 与MemoryAccessor的接口

---

## Step 4: 实现MemoryAccessor模块

**任务描述**: MemoryAccessor从data memory获取数据

**实现要点**:
1. 得到memory输出并传递给writeback模块

**涉及文件**: `impl/gen_cpu/pipestage.py`

**[CKPT-4]**: 验证MemoryAccessor模块:
- memory读取数据的传递
- 与WriteBack的接口

---

## Step 5: 实现WriteBack模块

**任务描述**: WriteBack将数据写回regfile

**实现要点**:
1. 把write data准备好，作为返回值传递给regfile_wrapper

**涉及文件**: `impl/gen_cpu/pipestage.py`

**[CKPT-5]**: 验证WriteBack模块:
- 写回数据的选择逻辑
- 与regfile_wrapper的接口

---

## Step 6: 在main.py中实现driver连接所有模块

**任务描述**: 创建顶层driver连接所有流水线模块

**实现要点**:
1. 实例化所有流水线stage
2. 实例化regfile_wrapper
3. 连接各模块的数据流和控制流
4. 初始化icache和dcache

**涉及文件**: `impl/gen_cpu/main.py`

**[CKPT-6]**: 验证顶层连接:
- 所有模块正确实例化
- 数据流正确连接
- 控制流正确
- 可以进行基础仿真测试

---

## Design Details Reference

### downstream: `regfile_wrapper`
已实现，待连线。
- 来自decoder: rs1_addr, rs2_addr, rd_write_en, rd_addr
- 来自writeback: rd_wdata
- 输出: rs1_data, rs2_data
