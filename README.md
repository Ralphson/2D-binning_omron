# 2D-binning_omron
二维装箱问题的python实现，多线程实时显示



输入数据格式：

- input.csv

|    图形类别     | 点1x | 点1y | 点2x | 点2y | 点3y | 点3y | 图形数量 |
| :-------------: | :--: | :--: | :--: | :--: | :--: | :--: | :------: |
| 0矩形 / 1三角形 |  0   |  0   |  0   |  3   |  3   |  3   |    2     |

输出数据格式：

- output.csv

|    图形类别     |   点1x   |   点1y   |  点2x   |   点2y   | 点3x | 点3y |
| :-------------: | :------: | :------: | :-----: | :------: | :--: | :--: |
| 0矩形 / 1三角形 | 30.26641 | 21.45843 | 30.0271 | 16.36503 |  31  |  12  |

*其中矩形的描述为从左下角开始逆时针取三个点*