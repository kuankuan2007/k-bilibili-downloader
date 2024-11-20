# k-bilibili-downloader

一个基于python的tkinter简易b站下载工具（真的很简易

## 起因

某朋友不知道在网上抄了一段什么代码，让我帮他重写UI

然后我看着那一坨像屎粑粑一样的代码陷入了沉思。。。

所以干脆我从头写一遍把

## 用法

### 安装依赖

### python

本软件在`Python 3.10`和`Python 3.12`上测试通过，其余信息待补充

#### pip

```bash
pip install -r requirements.txt
```

#### ffmpeg

保证此程序运行时能够通过`ffmpeg`指令直接调启ffmpeg

可以尝试使用此命令

```bash
ffmpeg -version
```
若能正常输出版本号，既表示ffmpeg可用

ffmpeg下载链接：https://ffmpeg.org/download.html

## 操作

1. 填入目标BV号/AV号或者直接填b站链接
2. 把你的b站cookie填进去
3. 点击下载，会尝试获取该视频的资料
4. 选择音频流/视频流开始下载

## 开源

本软件基于[MulanPSL-2.0](./LICENSE)协议开源