# todo

oct,27,17:00,tbd

## 

根据我下面设计的关键拓扑关系，来帮我实现缺失的还未完成的逻辑，每一段逻辑块的更新都视为ckpt，需要和我确认正误。
`impl/gen_cpu/main.py`，加入driver，连接不同的模块。
`impl/gen_cpu/downstreams.py`，不同级的流水线模块想要调用统一的外部模块的枢纽模块（比如regfile），或是进行bypass相关的包装。
`impl/gen_cpu/pipestage.py`，流水线模块，asyncall连接会把数据通过fifo传给下一个模块。

### design details

- downstream: `regfile_wrapper`
已实现，待连线。
来自decoder：
rs1_addr,
rs2_addr,
rd_write_en,
rd_addr,

来自writeback：
rd_wdata

- pipestage: `Fetchor`
```get instruction from icache```
待完整实现，
1. 接受driver的激励，初始化开始从头读instruction memory中的指令。
2. 传递给decoder实际fetch的指令所对应的address。

- pipestage: `Decoder`
```decoding the instruction into control signals for other modules```
待完整实现，
1. i cache读出的指令作为regarray传递进来，然后输入给decoder译码。
2. 把不同的decoder输出打包，作为return 传递出去。方便之后在downstream使用。

- pipestage: `Executor`
```exe signal to arthi modules```
待完整实现，
1. 调用ALU
2. 调用Adder
3. 设置data memory读取地址。

- pipestage: `MemoryAccessor`
```get data from data memory```
待完整实现，
1. 得到memory out并传递给writeback模块。

- pipestage: `WriteBack`
```write data to regfile```
待完整实现，
1. 把write data准备好，作为返回值传递给regfile_wrapper.
