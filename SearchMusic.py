# encoding:utf-8
import json
import requests
import re
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *

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

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
            
        content = e_context["context"].content
        reply = Reply()
        reply.type = ReplyType.TEXT

        # 处理酷狗点歌命令
        if content.startswith("酷狗点歌 "):
            song_name = content[5:].strip()  # 去除多余空格
            if not song_name:
                reply.content = "请输入要搜索的歌曲名称"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={song_name}&n="
            
            try:
                response = requests.get(url, timeout=10)
                songs = response.text.strip().split('\n')
                if songs and len(songs) > 1:  # 确保有搜索结果
                    reply_content = "🎵为你在酷狗音乐库中找到以下歌曲：\n\n"
                    for song in songs:
                        if song.strip():  # 确保不是空行
                            reply_content += f"{song}\n"
                    reply_content += f"\n请发送「酷狗听歌 {song_name} 序号」来播放对应歌曲"
                else:
                    reply_content = "未找到相关歌曲，请换个关键词试试"

                reply.content = reply_content

            except Exception as e:
                logger.error(f"[SearchMusic] 酷狗点歌错误: {e}")
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
                    reply.content = (
                        f"🎵 {song_info[1]}\n"  # 歌名
                        f"🎤 {song_info[2]}\n"  # 歌手
                        f"🔗 {song_info[3]}\n"  # 歌曲详情页
                        f"▶️ {song_info[4]}"    # 播放链接
                    )
                else:
                    reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

            except Exception as e:
                logger.error(f"[SearchMusic] 酷狗听歌错误: {e}")
                reply.content = "获取失败，请稍后重试"

        # 处理网易点歌命令
        elif content.startswith("网易点歌 "):
            song_name = content[5:].strip()
            if not song_name:
                reply.content = "请输入要搜索的歌曲名称"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={song_name}&n=&num=20"
            
            try:
                response = requests.get(url, timeout=10)
                songs = response.text.strip().split('\n')
                if songs and len(songs) > 1:  # 确保有搜索结果
                    reply_content = "🎵为你在网易音乐库中找到以下歌曲：\n\n"
                    for song in songs:
                        if song.strip():  # 确保不是空行
                            reply_content += f"{song}\n"
                    reply_content += f"\n请发送「网易听歌 {song_name} 序号」来播放对应歌曲"
                else:
                    reply_content = "未找到相关歌曲，请换个关键词试试"

                reply.content = reply_content

            except Exception as e:
                logger.error(f"[SearchMusic] 网易点歌错误: {e}")
                reply.content = "搜索失败，请稍后重试"

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
                img_match = re.search(r'±img=(.*?)±', content)
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
                
            url = f"https://www.hhlqilongzhu.cn/api/dg_shenmiMusic_SQ.php?msg={song_name}&n=&type=text"
            
            try:
                response = requests.get(url, timeout=10)
                songs = response.text.strip().split('\n')
                if songs and len(songs) > 1:  # 确保有搜索结果
                    reply_content = "🎵为你在神秘音乐库中找到以下歌曲：\n\n"
                    for song in songs:
                        if song.strip():  # 确保不是空行
                            reply_content += f"{song}\n"
                    reply_content += f"\n请发送「神秘听歌 {song_name} 序号」来播放对应歌曲"
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
                    # 只返回歌名、歌手和播放链接
                    reply.content = (
                        f"🎵 {song_info[1]}\n"  # 歌名
                        f"🎤 {song_info[2]}\n"  # 歌手
                        f"▶️ {song_info[4]}"    # 播放链接
                    )
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
            "🎵 音乐搜索和播放功能：\n\n"
            "1. 酷狗音乐：\n"
            "   - 搜索：发送「酷狗点歌 歌曲名称」\n"
            "   - 播放：发送「酷狗听歌 歌曲名称 序号」\n"
            "2. 网易音乐：\n"
            "   - 搜索：发送「网易点歌 歌曲名称」\n"
            "   - 播放：发送「网易听歌 歌曲名称 序号」\n"
            "3. 神秘音乐：\n"
            "   - 搜索：发送「神秘点歌 歌曲名称」\n"
            "   - 播放：发送「神秘听歌 歌曲名称 序号」\n"
            "注：序号在搜索结果中获取"
        )