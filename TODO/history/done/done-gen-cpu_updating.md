# Done Log: CPU Implementation Update

开始时间: oct,27,17:00
当前状态: 进行中

---

## Step 0: Todo修饰 ✓

**完成时间**: oct,27,17:00
**耗时**: ~3 min
**Token消耗**: ~22k tokens

**完成内容**:
- 阅读decorator-rules.md
- 分析现有代码结构
- 创建修饰后的todo文件到TODO/temp/
- 将原始todo分解为6个step，每个step都有对应的CKPT检查点

---

## 进度跟踪

- [x] Step 0: Todo修饰
- [ ] Step 1: 实现Fetchor模块
- [ ] Step 2: 完善Decoder模块
- [ ] Step 3: 实现Executor模块
- [ ] Step 4: 实现MemoryAccessor模块
- [ ] Step 5: 实现WriteBack模块
- [ ] Step 6: 实现main.py driver

---

## Step 1: 实现Fetchor模块的完整逻辑 ✓

**完成时间**: oct,27,17:xx
**耗时**: ~5 min
**Token消耗**: ~31k tokens

**完成内容**:
- 重写Fetchor.build方法
- 添加PC寄存器管理(自动递增)
- 实例化icache(SRAM)
- 实现从icache读取指令的逻辑
- 正确传递fetch_addr给decoder
- 返回icache.dout供decoder使用

**修改文件**:
- `impl/gen_cpu/pipestage.py:16-55`

**[CKPT-1创建]**: 已创建ckpt文件记录详细验证点

---

## Step 2: 完善Decoder模块的数据传递 ✓

**完成时间**: oct,27,17:xx
**耗时**: ~5 min
**Token消耗**: ~41k tokens

**完成内容**:
- 添加详细的函数文档注释
- 完善传递给Executor的控制信号(从5个增加到14个)
- 包含完整的ALU、Adder、Memory、Writeback控制信号
- 改进返回值，添加imm并调整顺序
- 添加代码注释分组，提高可读性

**修改文件**:
- `impl/gen_cpu/pipestage.py:65-159`

**[CKPT-2创建]**: 已更新ckpt文件记录详细验证点

---

## Step 3: 实现Executor模块的完整逻辑 ✓

**完成时间**: oct,27,18:xx
**耗时**: ~10 min
**Token消耗**: ~56k tokens

**完成内容**:
- 更新端口定义(从6个扩展到14个完整端口)
- 实现ALU输入选择逻辑(支持ZERO/RS1/RS2/IMM)
- 实现Adder输入选择逻辑(支持ZERO/RS1/PC/IMM)
- 实现Adder后处理(清除LSB用于JALR)
- 实例化dcache并设置读写控制
- 实现memory地址计算和写数据选择
- 传递所有必要信号给MemoryAccessor

**修改文件**:
- `impl/gen_cpu/pipestage.py:10-14` (新增导入)
- `impl/gen_cpu/pipestage.py:135-282` (完整重写Executor)

**[CKPT-3创建]**: 已更新ckpt文件记录详细验证点

---

## Step 4: 实现MemoryAccessor模块 ✓

**完成时间**: oct,27,18:xx
**耗时**: ~5 min
**Token消耗**: ~62k tokens

**完成内容**:
- 添加9个端口接收Executor的所有输出
- 实现完整的写回数据选择逻辑(6种选择)
- 支持ALU/IMM/ADDER/LOAD/LOAD_ZEXT8/PC_PLUS4
- 实现PC+4计算用于JAL/JALR返回地址
- 通过async_called传递rd和rd_data给WriteBack

**修改文件**:
- `impl/gen_cpu/pipestage.py:13` (新增WbDataSel导入)
- `impl/gen_cpu/pipestage.py:287-356` (完整实现MemoryAccessor)

**[CKPT-4创建]**: 已更新ckpt文件记录详细验证点

---

## Step 5: 实现WriteBack模块 ✓

**完成时间**: oct,27,18:xx
**耗时**: ~3 min
**Token消耗**: ~71k tokens

**完成内容**:
- 添加完整的类和方法文档注释
- 说明WriteBack作为最简单的流水线阶段
- 添加端口注释(rd, rd_data)
- 说明返回值用于连接regfile_wrapper

**修改文件**:
- `impl/gen_cpu/pipestage.py:358-386` (添加文档注释)

**[CKPT-5创建]**: 已更新ckpt文件记录详细验证点

---

## Step 6: 在main.py中实现driver连接所有模块 ✓

**完成时间**: oct,27,18:xx
**耗时**: ~20 min
**Token消耗**: ~89k tokens

**重要修正**:
- ❌ 最初错误实现为嵌套Module.build()
- ✓ 修正为top()普通函数，参考bypass.py模式

**完成内容**:
- 创建top()函数(135行，非Module)
- 按正确顺序实例化所有5个流水线阶段
- 按依赖顺序调用各模块的build方法
- 实现RegArray类型数据的正确连接(icache.dout, dcache.dout)
- 处理regfile的循环依赖(使用RegArray作为中间存储)
- 实现Value到RegArray的类型转换
- 添加命令行接口
- 添加详细的文档注释和连接说明

**创建文件**:
- `impl/gen_cpu/main.py` (全新文件，135行)

**[CKPT-6创建]**: 已更新ckpt文件记录详细验证点

---

## 任务总结

**总耗时**: ~50 min
**总Token消耗**: ~79k tokens
**完成的Steps**: 6个主要步骤

### 完成的工作

1. ✓ Step 0: 创建修饰后的todo文件
2. ✓ Step 1: 实现Fetchor模块(PC管理, icache实例化)
3. ✓ Step 2: 完善Decoder模块(完整控制信号传递，移除冗余Record包装)
4. ✓ Step 3: 实现Executor模块(ALU/Adder输入选择, dcache, 地址计算)
5. ✓ Step 4: 实现MemoryAccessor模块(写回数据选择, RegArray传递修正)
6. ✓ Step 5: 完善WriteBack模块(文档注释)
7. ✓ Step 6: 实现main.py driver(所有模块连接)

### 关键设计决策

- RegArray传递: SRAM.dout必须作为返回值在外部连接
- 移除冗余包装: 直接使用decoder输出，不需要Record包装
- 循环依赖处理: 使用RegArray作为中间存储处理regfile反馈回路

### 文件修改统计

- 修改: `impl/gen_cpu/pipestage.py` (完整重写5个流水线模块)
- 创建: `impl/gen_cpu/main.py` (152行新文件)
- 创建: `TODO/temp/todo-gen-cpu_updating.md`
- 创建: `TODO/temp/done-gen-cpu_updating.md`
- 创建/更新: `TODO/temp/ckpt-gen-cpu_updating.md` (6个检查点)

---

## Step 6 重要修正 (第二轮)

**修正时间**: oct,27,19:xx
**耗时**: ~10 min
**Token消耗**: ~101k tokens

**修正内容**:
1. ✓ 修正regfile写回连接: WriteBack返回值直接传给regfile，移除中间RegArray
2. ✓ 简化Decoder返回值: 只返回(rs1_addr, rs2_addr, imm)
3. ✓ 增加WriteBack返回值: 返回(rd, rd_data, wb_en)
4. ✓ 消除不必要的RegArray转换: RegOut可直接作为Array使用
5. ✓ 修正MemoryAccessor: 传递wb_en给WriteBack

**修改文件**:
- `impl/gen_cpu/pipestage.py` (Decoder返回值, MemoryAccessor传递, WriteBack返回值)
- `impl/gen_cpu/main.py` (regfile连接, 数据流修正)

**数据流**:
- Decoder: 返回rs地址和imm，通过流水线传递rd_addr和wb_en
- WriteBack: 返回rd, rd_data, wb_en
- regfile: 读地址来自Decoder，写控制来自WriteBack

---

## 下一步

[等待用户确认] 所有模块已实现完成，需要:
1. 验证整体设计正确性
2. 是否需要编写测试用例
3. 是否需要生成Verilog进行验证
