# Reference for Normal Signal Relationships

## pipe.py - 基本流水线传递

Driver ---> Stage1 ---> Stage2

- **数据流**: cnt[i]@cycle(i) → Stage1 → Stage2 接收 cnt[i-1]@cycle(i)
- **时序**: Stage2 收到的数据比 Stage1 晚 1 周期
- **验证**: 同一周期内 stage1 与 stage2 的数据值相差 1

```
a[i]@cycle(i) -----> fifo -----> a[i]@cycle(i+1)
```


## bypass.py - 旁路与寄存器写入

Driver ---> Stage1 ---> Stage2
              |  |
              |  +--------> reg[0] (写入)
              v
         Downstream (bypass监测)

- **FIFO 旁路**: fifo_bypass@cycle(N) = fifo_data@cycle(N+1)
- **寄存器旁路**: reg_wr_bypass@cycle(N) = reg[0]@cycle(N+1)
- **拓扑**: Downstream 同时观测流水线传递前后的数据，验证旁路数据提前 1 周期

```
a[i]@cycle(i) -----> fifo -----> a[i]@cycle(i+1)
     |                                  |
     +-------- downstream ---------------+
```


## stall.py - 条件停顿

Driver ---> Stage1 (wait_until) ---> Stage2

- **停顿条件**: Stage1 只在 `data % 3 == 0` 时向 Stage2 传递数据
- **控制信号**: wait_until 阻塞流水线，直到条件满足
- **验证**: Stage2 只接收能被 3 整除的数据

```
module1 ( wait_until(cond) ) ---> fifo ---> module2
```


## branch.py - 条件分支与合并

         +---> Branch1 --+
Driver --|               |--> Merging (downstream)
         +---> Branch2 --+

- **分支条件**:
  - valid1 = (cnt[0:1] == 2) → Branch1
  - valid2 = (cnt[0:1] == 3) → Branch2
- **合并逻辑**: Merging 根据 valid1/valid2 选择性接收两个分支的数据
- **拓扑**: 单源多路分支，条件合并

```
         +---> branch1 --+
driver --|               |--> merging
         +---> branch2 --+
        (valid1/valid2)
```

