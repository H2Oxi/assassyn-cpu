# todo-gen-base_test

oct,27,20:30,tbd

## 实现base test来测试整个cpu

### Step 1: 分析参考代码结构

分析`assassyn/examples/minor-cpu/src/main.py`中的driver和测试编写方式，理解以下关键点：
- SysBuilder的使用方式
- build_cpu和run_cpu函数的分离设计
- init_workspace的工作流程
- workload文件的加载机制（.exe, .data, .config, .sh）
- 测试验证的check()函数实现

**[ckpt-1]** 记录minor-cpu测试架构的关键设计模式

### Step 2: 分析测试目标代码

分析`impl/gen_cpu/main.py`的实现：
- top()函数的参数和返回值
- 与minor-cpu的main.py的差异
- 需要什么样的wrapper来适配测试框架

**[ckpt-2]** 确认gen_cpu的测试接口设计

### Step 3: 实现test_base.py的基础框架

在`test/sw/test_base.py`中实现：
- 导入必要的模块（SysBuilder, config, elaborate等）
- 定义工作空间路径
- 实现cp_if_exists辅助函数（复制workload文件）
- 实现init_workspace函数（初始化测试工作空间）

**[ckpt-3]** 基础框架代码已实现

### Step 4: 实现build_cpu函数

实现build_cpu函数：
- 创建SysBuilder('gen_cpu')
- 在SysBuilder上下文中调用top()函数
- 配置config参数（参考minor-cpu）
- 调用elaborate生成simulator和verilog
- 使用utils.build_simulator编译simulator
- 返回sys, simulator_binary, verilog_path

**[ckpt-4]** build_cpu函数已实现并可编译

### Step 5: 实现check函数

实现check()函数用于验证测试结果：
- 参考minor-cpu的check()实现
- 使用find_pass.sh脚本验证输出
- 处理返回值和异常

**[ckpt-5]** check函数已实现

### Step 6: 实现run_cpu函数

实现run_cpu函数：
- 读取workload.config并处理offset
- 运行simulator（utils.run_simulator）
- 调用check()验证结果
- 运行verilator仿真（utils.run_verilator）
- 再次check()验证verilog仿真结果

**[ckpt-6]** run_cpu函数已实现

### Step 7: 实现主测试函数

实现__main__部分：
- 调用build_cpu(depth_log=9)构建CPU一次
- 定义workload路径为`resources/riscv/benchmarks/`
- 初始化workspace加载0to100.exe
- 调用run_cpu执行测试
- 处理测试通过/失败的输出

**[ckpt-7]** 主测试流程已实现

### Step 8: 执行测试并验证

运行测试：
- 执行`python test/sw/test_base.py`
- 检查0to100.exe的测试是否通过
- 验证simulator和verilator输出一致
- 确认所有断言通过

**[ckpt-8]** 测试执行成功，0to100.exe通过验证

### Step 9: 代码审查和清理

- 检查代码风格是否符合项目规范
- 添加必要的文档字符串
- 确认没有多余的调试输出
- 验证代码可读性

**[ckpt-9]** 代码审查完成，准备提交
