# ckpt-gen-base_test_update

## ckpt-1: test/sw/test_base.py 完成首次修改并梳理新的校验逻辑

### 修改文件
- `test/sw/test_base.py`

### 修改内容
1. **引入内部校验依赖**：删除对 `subprocess` 的依赖，改为导入 `re` 以及 `LogChecker`/`RegexExtractor`/`LogRecord`，并定义 `WRITEBACK_PATTERN` 统一解析写回日志。
2. **重写 `check()`**：读取 `raw.log` 与 `.workspace/workload.data`，通过 `LogChecker` 聚合 `[writeback]` 记录，统计 x14 累加和值及最后一次 x10 写回；当校验失败时输出包含周期时间戳的详细错误信息。
3. **新增辅助函数**：实现 `_parse_writeback_record`（生成带 `cycle` 元数据的 `LogRecord`）与 `_load_reference_sum`（兼容十六进制/十进制数据行）。

### 设计说明
- 解析逻辑直接复用了项目统一的 `LogChecker` 框架，便于未来扩展更多写回字段检查。
- 错误信息会携带从日志中提取的 `cycle` 值，满足“报错需带时间戳”的调试需求。
- 摆脱 shell 脚本依赖，测试在纯 Python 环境即可执行并验证。

### 待确认
- 请确认新的 Python 校验逻辑与时间戳输出形式满足需求，若无问题可继续 Step 4 的验证。

