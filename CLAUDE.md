# Assassyn-CPU

Assassyn-CPU is a project for exploring the cpu design with LLM's help, while using assassyn as a unified programming interface.

## Debugging Guideline

每当使用python debug时，请注意只截取末尾50行来debug。如果信息不足再进一步截取更长的输出信息。

## Todo

每当实现todo时，要先创建对应的done文件，每完成一个todo内的step都要在done文件进行更新和记录。
当完整的完成了todo文件和done文件，请把todo文件移动到`TODO/todo_history`,done文件移动到`TODO/done_history`。
请对每个step的完成时间花费和tokens花费记录在done文件中。