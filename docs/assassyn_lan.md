# assassyn language simple ref

## 模块

我们有大致三种模块，

### `module`

port是fifo out，在build内pop值出来使用。
build只能接受regarray输入。
实现高度同步的操作以及数据流。

### `downstream`

build可以接受value。
不存在port这种有时序依赖性的端口，实现并发的操作。

### `ExternalSV`

外部模块，
regout是存在时序的只读regarray。
wireout和wirein都是value类型变量。
实现常用ip的定制化。


## 关键语法

### 变量类型

#### `RegArray`



#### `Value`


### 赋值语句

#### `sel`

#### `case`

### 条件控制

#### `condition`


### 语法糖

#### `fsm`

### 结束控制

#### `finish`
