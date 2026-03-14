# 软件使用指南

## 1 Python 熟练用户

如果你对python的程序、命令行以及虚拟环境比较熟练，只需要在你的环境里下载几个包即可。他们是：`numpy`,` pandas`,` matplotlib`,` PyQt5`.

然后将整个文件`git`或者解压缩到本地，运行`transfer_app.py`即可。

## 2 Python 陌生用户

### 2.1 python 程序安装

如果你对python不太熟悉，或者电脑上根本没有python，可以参考下面的步骤进行安装。

* 首先，如果你忘记了以前有没有装过python，可以先调出命令行，这在windows中是`win`+`R`，然后输入command，点击确定。在命令行中，输入

```
python --version
```

​	如果反馈类似

```
Python 3.x.x
```

​	说明电脑里有python环境。

​	如果不然，说明没有python。

* 如有，看2.2。
* 如果没有，请在https://www.python.org/downloads/
 这个目录下找到至少`3.X`的项目（推荐3.10及以上）,点击进去，找到对应的`win`或者`mac`系统进行下载。 Windows 用户通常选择 "Windows installer (64-bit，而不是32-bit)"。

* 运行下载好的 `.exe` 安装程序。

* 在安装界面底部，务必勾选 **Add Python to PATH**（将 Python 添加到环境变量）。**解释**：如果不勾选这一项，后续在黑窗口输入命令时会提示“不是内部或外部命令”。

* 点击 "Install Now"。
* 安装好后，看2.1开头验证一下是否安装成功。如果安装失败，上网搜一下。

### 2.2 安装库

在命令行里，输入

```pip install
pip install numpy pandas matplotlib PyQt5
```

如果出现

```
pip is not recognized
```

说明上面**Add Python to PATH**被你忽略了。上网搜一下解决办法。

### 2.3 软件启动

上面都做好了之后，如果会命令行（或者搜教程速通一下命令行，cd到软件目录下），运行transfer_app.py即可。

如果不会，在文件夹内部的空白处右键单击，点击在终端中打开。

![image-20260314234824350]([[figs\1.png](https://github.com/WuYudaPKU/Trans_Curve_Process/blob/main/figs/1.png?raw=true)

然后会跳出来一个命令行，输入
```
python transfer_app.py
```
即可启用软件。

### 2.4 软件功能

* 目前软件支持将课题组的转移曲线通过`add file`直接上传，在该栏目下也支持批量选择。

* 通过`add folder`可以上传文件夹。

> 注意：请不要上传除了转移曲线之外的CSV文件，因为写的时候没考虑，所以不知道会出什么bug。

* 在运行之前，需要手工选择输出路径。

* 单击`Run`，会卡一下（软件在运行），然后输出一大堆东西到输出路径里。这包括：

  * 一张总表，每个trans文件对应表格里的一行，标题就是trans文件名，后面是转移曲线的各种特征。

  * 多张图，图片的名称前缀是trans的文件名，用于可视化以及校准特征提取的过程。


> 目前，软件支持n型和p型材料，支持滞回线（会保存成Sweep1和Sweep2，分别对应前一半和后一半）。

---

`2026-03-15`更新

支持输入WLd以计算 $\mu C^*$ 。支持每个文件分别设置WLd。

## 3 声明

1. 欢迎使用。
2. 欢迎和我提各种各样的bug！
3. 请勿商用。
4. 该项目仅供参考，请认真校对，数据出现问题概不负责。
