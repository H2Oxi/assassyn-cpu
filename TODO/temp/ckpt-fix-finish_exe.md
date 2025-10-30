# ckpt-fix-finish_exe

## ckpt-pipestage: Decoder/Executor 终止路径

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 关键改动
- 引入 `InstrFormat`，在 decoder 中通过 raw instruction 提取 `imm12/rs1/rd`
- 识别 `ecall`、`ebreak`，在满足 `imm12 ∈ {0,1}` 且 `rs1/rd == x0` 时产生 `finish_hint`
- 扩展 executor 端口以接收 `finish_hint`，并在检测到终止指令时记录日志并调用 `finish()`
- 新增自循环检测：对 `AddrPurpose ∈ {BR_TARGET, IND_TARGET, J_TARGET}` 的指令，当跳转目标等于自身地址（且分支被判定为 taken）时触发 `finish()`

### 验证要点
- 正常指令应继续工作，`finish_hint` 仅在系统终止指令时置位
- 分支和跳转指令仅在真实自环并被执行时结束仿真
- 请求用户确认上述行为是否符合预期，再决定是否进入 Step 3（运行验证）
