# Assassyn-CPU

Assassyn-CPU is a project for exploring the cpu design with LLM's help, while using assassyn as a unified programming interface.

## Debugging Guideline

每当使用python debug时，请注意只截取末尾50行来debug。如果信息不足再进一步截取更长的输出信息。

## Todo修饰

参考`TODO/todo-rules.md`的修饰规则指导。
进行todo修饰时，请先根据指定的`TODO/`下的todo原始文件,在`TODO/temp`创建对应的done文件，每完成一个todo内的step都要在done文件进行更新和记录。

## Todo执行

每当实现todo时，要先创建对应的done文件，每完成一个todo内的step都要在done文件进行更新和记录。当遇到ckpt标记时，需要创建对应的ckpt文件记录更新，并暂停等待用户交互确认上一步的完成情况以及确认是否继续执行下一步。
当完整的完成了`TODO/temp`todo文件，请把todo文件移动到`TODO/history/todo`,done文件移动到`TODO/history/done`。

请对每个step的完成时间花费和tokens花费记录在done文件中。
