# todo

oct,27,21:10,tbd

## 修复 `test/sw/test_base.py`

需要继续修复，
1. 我们需要在`test/sw/test_base.py`中 设计 driver，并设置比如当cnt[0]>10 的时候才开始async call fetchor，让整个cpu 开始运行。 这里可以参考 `test/sw/test_decoder.py`.

2. 我们需要在impl中加入log，需要对exe中的fetch addr进行log，然后还需要对decoder中读到的ins data进行log，然后还要对writeback中每次要写的rd和rd data进行log。

3. 请查看`resources/riscv/benchmarks/0to100.sh`中的验证逻辑，他实际上就是使用了writeback的log来进行的验证，这里的脚本原本是对于`assassyn/examples/minor-cpu/src/writeback.py`匹配的验证脚本。请参考这个设计匹配的验证脚本。

4. 运行验证。


5. 新创建一个downstream模块。`class jump_predictor_wrapper(Downstream)`
  1. 当遇到跳转相关的指令时，只有当跳转判断完确认更新对的fetch address后，才让decoder中的valid再次生效，也即，我们需要在decoder中译码得到is_jump，并管理一个regarray类型的变量，让valid和这个reg与起来。确保当出现jump指令的时候，只call一次，之后要等到downstream模块的地址更新信号有效的时候且真正作用于fetchor后的下一个cycle，才能继续正常确认valid。
  2. 我们需要将跳转信号 + 跳转目标地址（adder_result）反馈给这个downstream模块，并在这个downstream模块内管理regarray变量，regarray变量作为fetchor.build的输入，来控制fetchor实际传递给icache的地址。