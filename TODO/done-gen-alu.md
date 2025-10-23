# done1 - ALU实现完成

oct,23,完成时间

## 完成内容

### 1. ✅ 规范了 `impl/ip/ips.py` 中ALU对应io口的数据类型和注释

**文件位置**: `impl/ip/ips.py:15-30`

**主要修改**:
- 修正了端口方向：`alu_op` 和 `cmp_op` 从 `WireOut` 改为 `WireIn`
- 规范了数据类型：
  - `alu_in1: WireIn[UInt(32)]` - ALU第一操作数输入
  - `alu_in2: WireIn[UInt(32)]` - ALU第二操作数输入
  - `alu_op: WireIn[UInt(4)]` - ALU操作码输入（4位支持9种操作）
  - `cmp_op: WireIn[UInt(3)]` - 比较器操作码输入（3位支持6种比较）
  - `alu_out: WireOut[UInt(32)]` - ALU运算结果输出
  - `cmp_out: WireOut[Bits(1)]` - 比较器结果输出
- 为每个io变量添加了详细的中文注释
- 在注释中明确了操作码编码：
  - ALU: 0=ADD, 1=SUB, 2=AND, 3=OR, 4=XOR, 5=SLL, 6=SRL, 7=SRA, 8=SLTU
  - CMP: 0=EQ, 1=NE, 2=LT, 3=GE, 4=LTU, 5=GEU, 6=NONE

### 2. ✅ 创建了 `impl/ip/ip_repo/alu.sv` 模块

**文件位置**: `impl/ip/ip_repo/alu.sv`

**设计特点**:
- **可综合设计**: 使用 `always_comb` 组合逻辑块
- **完整功能**: 实现了rv32i.csv中所有ALU相关操作
- **9种ALU操作**:
  - ADD: 加法运算
  - SUB: 减法运算
  - AND: 按位与
  - OR: 按位或
  - XOR: 按位异或
  - SLL: 逻辑左移
  - SRL: 逻辑右移
  - SRA: 算术右移（保留符号位）
  - SLTU: 无符号小于比较
- **6种比较操作**:
  - EQ: 相等比较
  - NE: 不等比较
  - LT: 有符号小于
  - GE: 有符号大于等于
  - LTU: 无符号小于
  - GEU: 无符号大于等于
- **正确处理**:
  - 移位操作使用低5位 `shamt = alu_in2[4:0]`
  - 算术右移使用 `$signed()` 保留符号
  - 有符号比较使用 `$signed()` 进行类型转换
  - 无符号比较直接使用逻辑比较

### 3. ✅ 创建了 `test/unit-test/ip/test_alu.py` 测试文件

**文件位置**: `test/unit-test/ip/test_alu.py`

**测试框架结构**:
- **Driver模块**:
  - 使用counter生成测试序列
  - 覆盖边界情况: 0, 0xFFFFFFFF(-1), 0x7FFFFFFF(最大正数), 0x80000000(最小负数)
  - 针对不同操作类型设计专门测试用例（算术、逻辑、移位、比较）

- **ForwardData模块**:
  - 支持可配置位宽（32位用于数据，4位用于alu_op，3位用于cmp_op）
  - 转发4路数据流到ALU模块

- **ALU Downstream模块**:
  - 实例化ExternalALU
  - 使用 `.optional()` 提供默认值
  - 输出详细日志格式: `[test] alu_in1:X|alu_in2:Y|alu_op:Z|cmp_op:W|alu_out:A|cmp_out:B`

- **ref_alu黄金模型**:
  - Python实现所有9种ALU操作
  - 正确处理32位有符号/无符号运算
  - 使用 `to_signed32()` 和 `to_unsigned32()` 进行类型转换
  - 移位操作正确处理移位量（取低5位）

- **ref_cmp黄金模型**:
  - Python实现所有6种比较操作
  - 正确区分有符号和无符号比较

- **check_raw验证函数**:
  - 解析日志输出
  - 逐行验证ALU和比较器输出
  - 使用断言确保99个测试用例全部通过
  - 提供详细的错误信息

**测试覆盖**:
- ✅ 边界值测试
- ✅ 有符号/无符号运算正确性
- ✅ 所有ALU操作类型
- ✅ 所有比较操作类型
- ✅ 移位操作（包括算术右移）

## 符合规范

1. ✅ 按照 `resources/riscv/isa/rv32i.csv` 规范实现
2. ✅ SystemVerilog设计可综合
3. ✅ 测试符合 `test/unit-test/unit-test.md` 规范
4. ✅ 参考了 `test/unit-test/ip/test_adder.py` 的测试框架

## 相关文件

- 修改: `impl/ip/ips.py`
- 新建: `impl/ip/ip_repo/alu.sv`
- 新建: `test/unit-test/ip/test_alu.py`
