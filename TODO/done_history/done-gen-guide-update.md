# done-gen-guide-update

oct,23,:,

## what I have done

1. 给`test/hw/unit-test/guidance/stall.py`写check，检测stage2出现的data是否满足stall_cond的条件即可。即assert data满足stall条件。
2. branch.py 目前有bug , 请查明bug原因。 修复bug后 ，写check。 我希望的merge的检测条件是，确保每次触发branch的data最后都能够被merge stage收集到。

