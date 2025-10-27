# todo

oct,27,12:00,tbd

##

对于`impl/gen_cpu/submodules.py`,我们和imm相关的接口现在是怎样设计的，我怎样把sel和imm结合起来确定后续模块实际使用的imm值？我们之前理应已经把imm的逻辑优化成所有种类都在sv源文件内被预处理以确保不同情况下直接使用imm都是可以支持的。请再次检查确认。请仔细思考分析当前的insdecoder所有的接口在被使用的时候如何和后续的模块连接，这里的模块指在`impl/ip/ips.py`内的所有module。确认是否还有设计不合理的端口。



 