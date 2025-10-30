# todo

oct,29,13:00,tbd

## 支持以下场景下finish cpu

修改文件`impl/gen_cpu/pipestage.py`

1. decoder检测到下列指令，push给executor，在executor检测，如果检测到了就触发finish()
ebreak
halt
ecall

2. 在executor检测，如果是跳转指令且目标地址还是跳转指令自己的地址，即陷入死循环，也要触发finish。

## ref

参考文件：`docs/assassyn_lan.md`