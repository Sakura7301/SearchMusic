# SearchMusic

## 基本信息
插件名称：SearchMusic
作者：Lingyuzhou
版本：2.0

## 插件更新日志
v3.0
- 🎴 新增音乐分享卡片功能，支持显示歌曲封面
- 🔄 替换了失效的神秘音乐API，改为使用汽水音乐API
- 🎵 新增随机点歌/听歌功能，支持音乐卡片和语音消息
v2.0
- 🎵 新增直接播放功能，支持在聊天中播放音乐
- 💾 新增了临时文件管理（通过gewechat_channel.py实现）
v1.0
- 🎵 支持三大音乐平台：酷狗、网易、神秘音乐
- 🔍 支持音乐搜索和播放链接获取

## 使用示例
![image](https://github.com/user-attachments/assets/a0395607-325a-4516-9c79-13449447b41b)

![image](https://github.com/user-attachments/assets/358998e0-eb65-4456-af5f-5ed3c8e1d23c)

![image](https://github.com/user-attachments/assets/a71ef877-f776-4289-956e-787a77312156)


## 使用方法

### 1. 酷狗音乐
- 搜索歌曲：发送 酷狗点歌 歌曲名称
- 音乐卡片：发送 酷狗点歌 歌曲名称 序号（返回音乐卡片）
- 语音播放：发送 酷狗听歌 歌曲名称 序号（返回语音消息）

### 2. 网易音乐
- 搜索歌曲：发送 网易点歌 歌曲名称
- 音乐卡片：发送 网易点歌 歌曲名称 序号（返回音乐卡片）
- 语音播放：发送 网易听歌 歌曲名称 序号（返回语音消息）

### 3. 汽水音乐
- 搜索歌曲：发送 汽水点歌 歌曲名称
- 音乐卡片：发送 汽水点歌 歌曲名称 序号（返回音乐卡片）
- 语音播放：发送 汽水听歌 歌曲名称 序号（返回语音消息）

### 4. 随机歌单
- 音乐卡片：发送 随机点歌（返回音乐卡片）
- 语音播放：发送 随机听歌（返回语音消息）

## 安装和使用教程
该插件需要在最新版dify-on-wechat基础之上修改gewechat代码，详细教程请查看文档
https://rq4rfacax27.feishu.cn/wiki/L4zFwQmbKiZezlkQ26jckBkcnod?fromScene=spaceOverview
