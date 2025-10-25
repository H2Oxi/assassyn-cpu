# todo1 

oct,23,14:30,done

## what I want you do

1. 这个的中alu开头的变量是可能涉及到的使用情况，`resources/riscv/isa/rv32i.csv`，请你根据这个表格规范`impl/ip/ips.py`中ALU对应io口的数据类型，以及对每个io变量的注释说明。

2. 根据规范后的io说明，在`impl/ip/ip_repo`创建并撰写alu.sv. 要求设计规范可综合。

3. 根据`test/unit-test/unit-test.md`规范，在``test/unit-test/ip`下创建并撰写test_alu.py. 要求符合unit-test设计规范。可参考同文件下其他文件。