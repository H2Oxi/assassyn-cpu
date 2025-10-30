# todo

oct,29,11:20,tbd

## 更新 `test/sw/test_base.py` 测试

请参考`docs/testing/stimulus_validator_template.md`. 实际上我们test_base 的driver已经比较简单，但是我们目前的check是借用了`resources/riscv/benchmarks/0to100.sh`来实现的，我希望这里能够把check显示的交给我们最新支持的checker来实现，而不再需要借助这个外部脚本。

并且我希望如果触发报错，能够记录并输出这个报错所对应的时间戳。我希望我们目前的valider能够支持检查错误时得到时间戳这个功能。
