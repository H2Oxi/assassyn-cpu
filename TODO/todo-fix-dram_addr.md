# todo

oct,29,17:20,tbd

##
更新`impl/gen_cpu/pipestage.py`.
对executor.build 加入一个输入参数，地址的offset。
输入给dcache的物理地址应该要减去这个offset。
对于`test/sw/test_base.py`来说应该是这个offset是` 0xb8`