# 这是一个描述todo文件在本项目中功能的文件。

## todo任务种类

- fix 对某项已完成的功能模块进行修复
- gen 涉及到impl设计文件的生成
- dev 不涉及impl，但会生成test文件或者模版文件，用于加速开发流程

## 文件结构

- TODO/
  |- history/               # 历史被完成的todo和done文件
  |- temp/                  # 被agent修饰过的附带checkpoint的step-wise的todo文件，以及工作中的ckpt文件和done文件
  `- todo-markdown-files... # 用户手写的todo草稿文件 ...

## todo文件修饰要求

### step-wise

尽可能确保把原始任务拆解成方便验证的子步骤中，即实现todo 到 todo list的转换。

### ckpt规则

每在一次todo中对某一个文件完成了第一次修动，需要创建对应的ckpt文件对这次修改进行说明。并且ckpt记号需要直接加进修饰后的todo文件。
