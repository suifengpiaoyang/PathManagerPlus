# PathManagerPlus

一个用来管理文件，文件夹，链接等路径的软件。

## 安装方法

### 从安装包安装

点击对应的 .exe 安装包进行安装。需要注意的是，软件需要安装在有写入权限的路径下。否则使用软件时尝试的配置文件和数据文件由于无法写入会产生一些意外行为。

### 从代码运行

#### 依赖环境

- Python 3.8+
- PySide2
- 无其他依赖

#### 安装相关的 python package

```
pip install pyside2
```

#### 将 .ui 生成对应的 .py 文件

进入 console 界面 ui 的路径(PathManagerPlus\PathManagerPlus\ui)下，运行

```
pyside2-uic main_window.ui -o main_window.py
pyside2-uic config_form.ui -o config_form.py
pyside2-uic add_path_form.ui -o add_path_form.py
```

#### 运行程序

通过 `python run.py` 可运行程序，或直接双击 run.py。默认情况下会弹出一个 console 界面，如果在 windows 下，想直接通过双击来使用，可以将 `run.py` 改成 `run.pyw`，这样就可以直接双击 `run.pyw` 运行并且没有 console 窗口了。

## 系统支持

| 操作系统   | 支持状态   | 说明                                                   |
| ---------- | ---------- | ------------------------------------------------------ |
| Windows 7  | ✅ 支持     | 已测试，运行良好                                       |
| Windows 10 | ✅ 支持     | 主开发/测试平台                                        |
| Windows 11 | ⚠️ 预计支持 | 尚未实机测试，理论兼容                                 |
| Linux      | 🚧 开发中   | 预留了结构，尚未测试与打包                             |
| macOS      | ❌ 不支持   | 当前 PySide2 无法正常安装；后续将迁移至 PySide6 以支持 |

> 关于 macOS 支持：由于 PySide2 在 macOS 上存在安装兼容性问题，计划在后续新分支中使用 PySide6 替代，完成后将支持 macOS。

## 使用方式

