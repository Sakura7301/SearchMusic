# encoding:utf-8
import json
import requests
import re
import os
import time
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from plugins import *
import random

@plugins.register(
    name="SearchMusic",
    desire_priority=100,
    desc="输入关键词'点歌 歌曲名称'即可获取对应歌曲详情和播放链接",
    version="1.0",
    author="Lingyuzhou",
)
class SearchMusic(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[SearchMusic] inited.")

    def download_music(self, music_url, platform):
        """
        下载音乐文件并返回文件路径
        :param music_url: 音乐文件URL
        :param platform: 平台名称（用于文件名）
        :return: 音乐文件保存路径或None（如果下载失败）
        """
        try:
            # 检查URL是否有效
            if not music_url or not music_url.startswith('http'):
                logger.error(f"[SearchMusic] 无效的音乐URL: {music_url}")
                return None

            # 发送GET请求下载文件，添加超时和重试机制
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            for retry in range(3):  # 最多重试3次
                try:
                    response = requests.get(music_url, stream=True, headers=headers, timeout=30)
                    response.raise_for_status()  # 检查响应状态
                    break
                except requests.RequestException as e:
                    if retry == 2:  # 最后一次重试
                        logger.error(f"[SearchMusic] 下载音乐文件失败，重试次数已用完: {e}")
                        return None
                    logger.warning(f"[SearchMusic] 下载重试 {retry + 1}/3: {e}")
                    time.sleep(1)  # 等待1秒后重试
            
            # 使用TmpDir().path()获取正确的临时目录
            tmp_dir = TmpDir().path()
            
            # 生成唯一的文件名，包含时间戳和随机字符串
            timestamp = int(time.time())
            random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
            music_name = f"{platform}_music_{timestamp}_{random_str}.mp3"
            music_path = os.path.join(tmp_dir, music_name)
            
            # 保存文件，使用块写入以节省内存
            total_size = 0
            with open(music_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        total_size += len(chunk)
            
            # 验证文件大小
            if total_size == 0:
                logger.error("[SearchMusic] 下载的文件大小为0")
                os.remove(music_path)  # 删除空文件
                return None
                
            logger.info(f"[SearchMusic] 音乐下载完成: {music_path}, 大小: {total_size/1024:.2f}KB")
            return music_path
            
        except Exception as e:
            logger.error(f"[SearchMusic] 下载音乐文件时出错: {e}")
            # 如果文件已创建，清理它
            if 'music_path' in locals() and os.path.exists(music_path):
                try:
                    os.remove(music_path)
                except Exception as clean_error:
                    logger.error(f"[SearchMusic] 清理失败的下载文件时出错: {clean_error}")
            return None

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
            
        content = e_context["context"].content
        reply = Reply()
        reply.type = ReplyType.TEXT

        # 处理酷狗点歌命令（搜索歌曲列表）
        if content.startswith("酷狗点歌 "):
            song_name = content[5:].strip()  # 去除多余空格
            if not song_name:
                reply.content = "请输入要搜索的歌曲名称"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            # 检查是否包含序号（新增的详情获取功能）
            params = song_name.split()
            if len(params) == 2 and params[1].isdigit():
                song_name, song_number = params
                url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={song_name}&n={song_number}"
                try:
                    response = requests.get(url, timeout=10)
                    content = response.text
                    song_info = content.split('\n')
                    
                    if len(song_info) >= 4:  # 确保有足够的信息行
                        reply.content = (
                            f"🎵 {song_info[1]}\n"  # 歌名
                            f"🎤 {song_info[2]}\n"  # 歌手
                            f"🔗 {song_info[3]}\n"  # 歌曲详情页
                            f"▶️ {song_info[4]}"    # 播放链接
                        )
                    else:
                        reply.content = "未找到该歌曲，请确认歌名和序号是否正确"
                except Exception as e:
                    logger.error(f"[SearchMusic] 酷狗点歌详情错误: {e}")
                    reply.content = "获取失败，请稍后重试"
            else:
                # 原有的搜索歌曲列表功能
                url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={song_name}&n="
                try:
                    response = requests.get(url, timeout=10)
                    songs = response.text.strip().split('\n')
                    if songs and len(songs) > 1:  # 确保有搜索结果
                        reply_content = " 为你在酷狗音乐库中找到以下歌曲：\n\n"
                        for song in songs:
                            if song.strip():  # 确保不是空行
                                reply_content += f"{song}\n"
                        reply_content += f"\n请发送「酷狗点歌 {song_name} 序号」获取歌曲详情\n或发送「酷狗听歌 {song_name} 序号」来播放对应歌曲"
                    else:
                        reply_content = "未找到相关歌曲，请换个关键词试试"
                    reply.content = reply_content
                except Exception as e:
                    logger.error(f"[SearchMusic] 酷狗点歌错误: {e}")
                    reply.content = "搜索失败，请稍后重试"

        # 处理网易点歌命令（搜索歌曲列表）
        elif content.startswith("网易点歌 "):
            song_name = content[5:].strip()
            if not song_name:
                reply.content = "请输入要搜索的歌曲名称"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            # 检查是否包含序号（新增的详情获取功能）
            params = song_name.split()
            if len(params) == 2 and params[1].isdigit():
                song_name, song_number = params
                url = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={song_name}&n={song_number}"
                try:
                    response = requests.get(url, timeout=10)
                    content = response.text
                    song_info = content.split('\n')
                    
                    if len(song_info) >= 4:  # 确保有足够的信息行
                        reply.content = (
                            f"🎵 {song_info[1]}\n"  # 歌名
                            f"🎤 {song_info[2]}\n"  # 歌手
                            f"🔗 {song_info[3]}\n"  # 歌曲详情页
                            f"▶️ {song_info[4]}"    # 播放链接
                        )
                    else:
                        reply.content = "未找到该歌曲，请确认歌名和序号是否正确"
                except Exception as e:
                    logger.error(f"[SearchMusic] 网易点歌详情错误: {e}")
                    reply.content = "获取失败，请稍后重试"
            else:
                # 原有的搜索歌曲列表功能
                url = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={song_name}&n=&num=20"
                try:
                    response = requests.get(url, timeout=10)
                    songs = response.text.strip().split('\n')
                    if songs and len(songs) > 1:  # 确保有搜索结果
                        reply_content = " 为你在网易音乐库中找到以下歌曲：\n\n"
                        for song in songs:
                            if song.strip():  # 确保不是空行
                                reply_content += f"{song}\n"
                        reply_content += f"\n请发送「网易点歌 {song_name} 序号」获取歌曲详情\n或发送「网易听歌 {song_name} 序号」来播放对应歌曲"
                    else:
                        reply_content = "未找到相关歌曲，请换个关键词试试"
                    reply.content = reply_content
                except Exception as e:
                    logger.error(f"[SearchMusic] 网易点歌错误: {e}")
                    reply.content = "搜索失败，请稍后重试"

        # 处理酷狗听歌命令
        elif content.startswith("酷狗听歌 "):
            params = content[5:].strip().split()
            if len(params) != 2:
                reply.content = "请输入正确的格式：酷狗听歌 歌曲名称 序号"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            song_name, song_number = params
            if not song_number.isdigit():
                reply.content = "请输入正确的歌曲序号（纯数字）"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={song_name}&n={song_number}"
            
            try:
                response = requests.get(url, timeout=10)
                content = response.text
                song_info = content.split('\n')
                
                if len(song_info) >= 4:  # 确保有足够的信息行
                    # 获取音乐文件URL（在第4行），并去除可能的"播放链接："前缀
                    music_url = song_info[4].strip()
                    if "播放链接：" in music_url:
                        music_url = music_url.split("播放链接：")[1].strip()
                    
                    # 下载音乐文件
                    music_path = self.download_music(music_url, "kugou")
                    
                    if music_path:
                        # 返回语音消息
                        reply.type = ReplyType.VOICE
                        reply.content = music_path
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = "音乐文件下载失败，请稍后重试"
                else:
                    reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

            except Exception as e:
                logger.error(f"[SearchMusic] 酷狗听歌错误: {e}")
                reply.content = "获取失败，请稍后重试"

        # 处理网易听歌命令
        elif content.startswith("网易听歌 "):
            params = content[5:].strip().split()
            if len(params) != 2:
                reply.content = "请输入正确的格式：网易听歌 歌曲名称 序号"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            song_name, song_number = params
            if not song_number.isdigit():
                reply.content = "请输入正确的歌曲序号（纯数字）"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={song_name}&n={song_number}"
            
            try:
                response = requests.get(url, timeout=10)
                content = response.text
                
                # 解析返回内容
                song_info = content.split('\n')
                
                if len(song_info) >= 4:  # 确保有足够的信息行
                    # 获取音乐文件URL（在第4行），并去除可能的"播放链接："前缀
                    music_url = song_info[4].strip()
                    if "播放链接：" in music_url:
                        music_url = music_url.split("播放链接：")[1].strip()
                    
                    # 下载音乐文件
                    music_path = self.download_music(music_url, "netease")
                    
                    if music_path:
                        # 返回语音消息
                        reply.type = ReplyType.VOICE
                        reply.content = music_path
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = "音乐文件下载失败，请稍后重试"
                else:
                    reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

            except Exception as e:
                logger.error(f"[SearchMusic] 网易听歌错误: {e}")
                reply.content = "获取失败，请稍后重试"

        # 处理神秘点歌命令
        elif content.startswith("神秘点歌 "):
            song_name = content[5:].strip()
            if not song_name:
                reply.content = "请输入要搜索的歌曲名称"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            # 检查是否包含序号（新增的详情获取功能）
            params = song_name.split()
            if len(params) == 2 and params[1].isdigit():
                song_name, song_number = params
                url = f"https://www.hhlqilongzhu.cn/api/dg_shenmiMusic_SQ.php?msg={song_name}&n={song_number}&type=text"
                try:
                    response = requests.get(url, timeout=10)
                    content = response.text
                    song_info = content.split('\n')
                    
                    if len(song_info) >= 4:  # 确保有足够的信息行
                        reply.content = (
                            f"🎵 {song_info[1]}\n"  # 歌名
                            f"🎤 {song_info[2]}\n"  # 歌手
                            f"🔗 {song_info[3]}\n"  # 歌曲详情页
                            f"▶️ {song_info[4]}"    # 播放链接
                        )
                    else:
                        reply.content = "未找到该歌曲，请确认歌名和序号是否正确"
                except Exception as e:
                    logger.error(f"[SearchMusic] 神秘点歌详情错误: {e}")
                    reply.content = "获取失败，请稍后重试"
            else:
                # 原有的搜索歌曲列表功能
                url = f"https://www.hhlqilongzhu.cn/api/dg_shenmiMusic_SQ.php?msg={song_name}&n=&type=text"
                try:
                    response = requests.get(url, timeout=10)
                    songs = response.text.strip().split('\n')
                    if songs and len(songs) > 1:  # 确保有搜索结果
                        reply_content = " 为你在神秘音乐库中找到以下歌曲：\n\n"
                        for song in songs:
                            if song.strip():  # 确保不是空行
                                reply_content += f"{song}\n"
                        reply_content += f"\n请发送「神秘点歌 {song_name} 序号」获取歌曲详情\n或发送「神秘听歌 {song_name} 序号」来播放对应歌曲"
                    else:
                        reply_content = "未找到相关歌曲，请换个关键词试试"
                    reply.content = reply_content
                except Exception as e:
                    logger.error(f"[SearchMusic] 神秘点歌错误: {e}")
                    reply.content = "搜索失败，请稍后重试"

        # 处理神秘听歌命令
        elif content.startswith("神秘听歌 "):
            params = content[5:].strip().split()
            if len(params) != 2:
                reply.content = "请输入正确的格式：神秘听歌 歌曲名称 序号"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            song_name, song_number = params
            if not song_number.isdigit():
                reply.content = "请输入正确的歌曲序号（纯数字）"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_shenmiMusic_SQ.php?msg={song_name}&n={song_number}&type=text&br=2"
            
            try:
                response = requests.get(url, timeout=10)
                content = response.text
                song_info = content.split('\n')
                
                if len(song_info) >= 4:  # 确保有足够的信息行
                    # 获取音乐文件URL（在第4行），并去除可能的"播放链接："前缀
                    music_url = song_info[4].strip()
                    if "播放链接：" in music_url:
                        music_url = music_url.split("播放链接：")[1].strip()
                    
                    # 下载音乐文件
                    music_path = self.download_music(music_url, "shenmi")
                    
                    if music_path:
                        # 返回语音消息
                        reply.type = ReplyType.VOICE
                        reply.content = music_path
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = "音乐文件下载失败，请稍后重试"
                else:
                    reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

            except Exception as e:
                logger.error(f"[SearchMusic] 神秘听歌错误: {e}")
                reply.content = "获取失败，请稍后重试"

        else:
            return

        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        return (
            " 音乐搜索和播放功能：\n\n"
            "1. 酷狗音乐：\n"
            "   - 搜索：发送「酷狗点歌 歌曲名称」\n"
            "   - 详情：发送「酷狗点歌 歌曲名称 序号」\n"
            "   - 播放：发送「酷狗听歌 歌曲名称 序号」\n"
            "2. 网易音乐：\n"
            "   - 搜索：发送「网易点歌 歌曲名称」\n"
            "   - 详情：发送「网易点歌 歌曲名称 序号」\n"
            "   - 播放：发送「网易听歌 歌曲名称 序号」\n"
            "3. 神秘音乐：\n"
            "   - 搜索：发送「神秘点歌 歌曲名称」\n"
            "   - 详情：发送「神秘点歌 歌曲名称 序号」\n"
            "   - 播放：发送「神秘听歌 歌曲名称 序号」\n"
            "注：序号在搜索结果中获取"
        )
