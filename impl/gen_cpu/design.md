# design plan for ai-generated minor-cpu

## block diagram

手写部分，数据流的同步结构，模块间的调用方式，大逻辑块的接口定义。

生成部分，每个逻辑块交给ai生成external 可综合的 systemverilog 设计。

一方面，pipestage包含了我们最基本的流水线stage。

涉及到多个stage间数据交互的复杂逻辑，我们都放到downstream里来实现。

被单一stage module所支配的submodule我们都放到submodules里。

## developing schedue

我先把整个minor cpu模块化重构到现在我所需要的这个结构下。

对于大部分内容仅保留接口，逻辑部分来靠ai辅助迭代。

### stage details

- downstream: `regfile`
- downstream: Fetching valid FSM `fetch_check`
- downstream: valid checker `valid_check`

#### Fetchor

get instruction from icache

- Memory: Instuction cache

#### Decoder

decoding the instruction into hard wires

- submodule: instruction decoder

#### Executor

exe signal to arthi modules

- submodule: ALU
- submodule: Adder
- Memory: Data cache

#### MemoryAccessor

get data from dcache

#### WriteBack

write data to dcache

## dreaming workflow for cpu impl generation

首先，一款cpu的核心，无疑是isa。

我们一定首先是需要一个isa表格来说明指令含义的。

有了指令集，我们接下来需要简单的约束或者说规划一下我们的基本组件，比如说regfile是怎样的结构，内存是怎样的映射，运算组件怎样构成，这些IP related的信息。

接下来，我们便需要细化各种设计间的取舍了。我们如何划分流水线，如何把不同的操作按照流水线划分出去。如何设计并行的数据交互消除纯粹流水线串行带来的bubbles。也许这一步可以变成设计的迭代过程。



what will LLM do, in such a circumstance?

ISA. + Components Constraints.  ---> Combinational design

workload related parallelism Constraints. ---> Sync design

我们有没有一种可能把常见的并行流，或者说数据同步的图， 准备好例子，让LLM模仿并自动发掘使用场景潜力。

首先，我们对于每个模块的关键变量以及接口，是一定有tag标记的，我们会标明某个变量他就是对应的比如说ALU 的输出结果，或者比如说是指令操作寄存器的序号。由此，我们就可以基于词，提示AI对某种功能tag下的变量或者接口，按照某种经典的拓扑（我们需要进行总结并准备模版）进行连接。



