# Assassyn-CPU

Assassyn-CPU is a project for exploring the cpu design with LLM's help, while using assassyn as a unified programming interface.

## Debugging Guideline

每当使用python debug时，请注意只截取末尾50行来debug。如果信息不足再进一步截取更长的输出信息。

## Todo workflow

todo，ckpt，done都是markdown格式的文件。

- todo 描述分步骤的任务和ckpt需要检查和验证的点。
- ckpt 描述需要验证的结论以及和用户交互确认的结论。
- done 记录每一步todo的完成情况，文件修改情况。

### Todo修饰

参考`TODO/decorator-rules.md`的修饰规则，在`TODO/temp`下创建修饰后的todo文件。

### Todo执行

在`TODO/temp`创建对应的done文件，每完成一个todo内的step都要在done文件进行更新和记录。当遇到ckpt标记时，需要创建对应的ckpt文件记录更新，并暂停等待用户交互确认上一步的完成情况以及确认是否继续执行下一步。请对每个step的完成时间花费和tokens花费记录在done文件中。

### Todo cleanup & log

当完整的完成了`TODO/temp`todo文件，请和用户确认任务是否完成成功，如果用户接受结果，则请把todo文件移动到`TODO/history/todo`,done文件移动到`TODO/history/done`，清空ckpt文件。