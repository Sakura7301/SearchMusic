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
import urllib.parse

@plugins.register(
    name="SearchMusic",
    desire_priority=100,
    desc="输入关键词'点歌 歌曲名称'即可获取对应歌曲详情和播放链接",
    version="3.0",
    author="Lingyuzhou",
)
class SearchMusic(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[SearchMusic] inited.")

    def construct_music_appmsg(self, title, singer, url, thumb_url="", platform=""):
        """
        构造音乐分享卡片的appmsg XML
        :param title: 音乐标题
        :param singer: 歌手名
        :param url: 音乐播放链接
        :param thumb_url: 封面图片URL（可选）
        :param platform: 音乐平台（酷狗/网易/抖音）
        :return: appmsg XML字符串
        """
        # 处理封面URL
        if thumb_url:
            # 不再移除抖音图片URL的后缀
            # 只确保URL是以http或https开头的
            if not thumb_url.startswith(("http://", "https://")):
                thumb_url = "https://" + thumb_url.lstrip("/")

            # 确保URL没有特殊字符
            thumb_url = thumb_url.replace("&", "&amp;")

        # 根据平台在标题中添加前缀
        if platform.lower() == "kugou":
            display_title = f"[酷狗] {title}"
            source_display_name = "酷狗音乐"
        elif platform.lower() == "netease":
            display_title = f"[网易] {title}"
            source_display_name = "网易云音乐"
        elif platform.lower() == "qishui":
            display_title = f"[汽水] {title}"
            source_display_name = "汽水音乐"
        else:
            display_title = title
            source_display_name = "音乐分享"

        # 确保URL没有特殊字符
        url = url.replace("&", "&amp;")

        # 使用更简化的XML结构，但保留关键标签
        xml = f"""<appmsg appid="" sdkver="0">
    <title>{display_title}</title>
    <des>{singer}</des>
    <action>view</action>
    <type>3</type>
    <showtype>0</showtype>
    <soundtype>0</soundtype>
    <mediatagname>音乐</mediatagname>
    <messageaction></messageaction>
    <content></content>
    <contentattr>0</contentattr>
    <url>{url}</url>
    <lowurl>{url}</lowurl>
    <dataurl>{url}</dataurl>
    <lowdataurl>{url}</lowdataurl>
    <appattach>
        <totallen>0</totallen>
        <attachid></attachid>
        <emoticonmd5></emoticonmd5>
        <fileext></fileext>
        <cdnthumburl>{thumb_url}</cdnthumburl>
        <cdnthumbaeskey></cdnthumbaeskey>
        <aeskey></aeskey>
    </appattach>
    <extinfo></extinfo>
    <sourceusername></sourceusername>
    <sourcedisplayname>{source_display_name}</sourcedisplayname>
    <thumburl>{thumb_url}</thumburl>
    <songalbumurl>{thumb_url}</songalbumurl>
    <songlyric></songlyric>
</appmsg>"""

        # 记录生成的XML，便于调试
        logger.debug(f"[SearchMusic] 生成的音乐卡片XML: {xml}")

        return xml

    def get_music_cover(self, platform, detail_url, song_name="", singer=""):
        """
        尝试获取歌曲封面图片URL
        :param platform: 平台名称（酷狗/网易/汽水）
        :param detail_url: 歌曲详情页URL
        :param song_name: 歌曲名称（可选，用于日志）
        :param singer: 歌手名称（可选，用于日志）
        :return: 封面图片URL，如果获取失败则返回默认封面
        """
        # 默认封面图片
        default_cover = "https://y.qq.com/mediastyle/global/img/album_300.png"

        try:
            # 根据不同平台使用不同的获取方式
            if platform == "kugou":
                # 尝试从酷狗音乐详情页获取封面
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(detail_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    # 使用正则表达式提取封面图片URL
                    cover_pattern = r'<img.*?class="albumImg".*?src="(.*?)"'
                    match = re.search(cover_pattern, response.text)
                    if match:
                        cover_url = match.group(1)
                        if cover_url and cover_url.startswith('http'):
                            logger.info(f"[SearchMusic] 成功获取酷狗音乐封面: {cover_url}")
                            return cover_url

            elif platform == "netease":
                # 尝试从网易云音乐详情页获取封面
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(detail_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    # 使用正则表达式提取封面图片URL
                    cover_pattern = r'<img.*?class="j-img".*?src="(.*?)"'
                    match = re.search(cover_pattern, response.text)
                    if match:
                        cover_url = match.group(1)
                        if cover_url and cover_url.startswith('http'):
                            logger.info(f"[SearchMusic] 成功获取网易音乐封面: {cover_url}")
                            return cover_url

            elif platform == "qishui":
                # 尝试从汽水音乐详情页获取封面
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(detail_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    try:
                        # 尝试解析JSON响应
                        data = json.loads(response.text)
                        if "cover" in data and data["cover"]:
                            cover_url = data["cover"]
                            # 检查是否是抖音域名的图片
                            if "douyinpic.com" in cover_url or "douyincdn.com" in cover_url:
                                logger.warning(f"[SearchMusic] 汽水音乐使用抖音域名图片，可能无法在微信中正常显示: {cover_url}")
                                # 不再使用备用图片
                                return cover_url
                            logger.info(f"[SearchMusic] 成功获取汽水音乐封面: {cover_url}")
                            return cover_url
                    except json.JSONDecodeError:
                        # 如果不是JSON，尝试使用正则表达式提取
                        cover_pattern = r'<img.*?class="cover".*?src="(.*?)"'
                        match = re.search(cover_pattern, response.text)
                        if match:
                            cover_url = match.group(1)
                            if cover_url and cover_url.startswith('http'):
                                # 检查是否是抖音域名的图片
                                if "douyinpic.com" in cover_url or "douyincdn.com" in cover_url:
                                    logger.warning(f"[SearchMusic] 汽水音乐使用抖音域名图片，可能无法在微信中正常显示: {cover_url}")
                                    # 不再使用备用图片
                                    return cover_url
                                logger.info(f"[SearchMusic] 成功获取汽水音乐封面: {cover_url}")
                                return cover_url

            # 对于汽水音乐，如果没有获取到封面，直接使用默认封面
            if platform == "qishui":
                logger.warning(f"[SearchMusic] 无法获取汽水音乐封面图片，使用默认封面: {song_name} - {singer}")
                return default_cover

            # 对于其他平台，尝试使用歌曲名称和歌手名称搜索封面
            if song_name and singer:
                # 尝试使用QQ音乐搜索API获取封面
                try:
                    search_url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={urllib.parse.quote(f'{song_name} {singer}')}&format=json&p=1&n=1"
                    response = requests.get(search_url, timeout=5)
                    if response.status_code == 200:
                        data = json.loads(response.text)
                        if "data" in data and "song" in data["data"] and "list" in data["data"]["song"] and data["data"]["song"]["list"]:
                            song_info = data["data"]["song"]["list"][0]
                            if "albummid" in song_info:
                                albummid = song_info["albummid"]
                                cover_url = f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{albummid}.jpg"
                                logger.info(f"[SearchMusic] 使用QQ音乐API获取到封面: {cover_url}")
                                return cover_url
                except Exception as e:
                    logger.error(f"[SearchMusic] 使用QQ音乐API获取封面时出错: {e}")

            logger.warning(f"[SearchMusic] 无法获取封面图片，使用默认封面: {song_name} - {singer}")
            return default_cover

        except Exception as e:
            logger.error(f"[SearchMusic] 获取封面图片时出错: {e}")
            return default_cover

    def extract_cover_from_response(self, response_text):
        """
        从API返回的内容中提取封面图片URL
        :param response_text: API返回的文本内容
        :return: 封面图片URL或None
        """
        try:
            # 尝试解析为JSON格式（汽水音乐API）
            try:
                data = json.loads(response_text)
                if "cover" in data and data["cover"]:
                    cover_url = data["cover"]
                    # 检查是否是抖音域名的图片
                    if "douyinpic.com" in cover_url or "douyincdn.com" in cover_url:
                        logger.warning(f"[SearchMusic] 检测到抖音域名图片，可能无法在微信中正常显示: {cover_url}")
                        # 不再使用备用图片
                    logger.info(f"[SearchMusic] 从JSON中提取到封面URL: {cover_url}")
                    return cover_url
            except json.JSONDecodeError:
                # 不是JSON格式，继续使用文本解析方法
                pass

            # 查找 ±img=URL± 格式的封面图片（抖音API格式）
            img_pattern = r'±img=(https?://[^±]+)±'
            match = re.search(img_pattern, response_text)
            if match:
                cover_url = match.group(1)
                # 检查是否是抖音域名的图片
                if "douyinpic.com" in cover_url or "douyincdn.com" in cover_url:
                    logger.warning(f"[SearchMusic] 检测到抖音域名图片，可能无法在微信中正常显示: {cover_url}")
                    # 不再使用备用图片
                # 不再移除后缀，保留完整的URL
                logger.info(f"[SearchMusic] 从API响应中提取到封面图片: {cover_url}")
                return cover_url
            return None
        except Exception as e:
            logger.error(f"[SearchMusic] 提取封面图片时出错: {e}")
            return None

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

        # 处理随机点歌和随机听歌
        if content.strip() in ["随机点歌", "随机听歌"]:
            self.handle_random_music(content, reply)

        # 处理酷狗、网易、汽水点歌和听歌命令
        elif content.startswith(("酷狗点歌 ", "酷狗听歌 ", "网易点歌 ", "网易听歌 ", "汽水点歌 ", "汽水听歌 ")):
            self.handle_platform_music(content, reply)

        else:
            return

        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def handle_random_music(self, content, reply:Reply):
        url = "https://hhlqilongzhu.cn/api/wangyi_hot_review.php"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "code" in data and data["code"] == 200:
                    title = data.get("song", "未知歌曲")
                    singer = data.get("singer", "未知歌手")
                    music_url = data.get("url", "")
                    thumb_url = data.get("img", "")

                    logger.info(f"[SearchMusic] 随机{'点歌' if content.strip() == '随机点歌' else '听歌'}获取成功: {title} - {singer}")

                    if content.strip() == "随机点歌":
                        appmsg = self.construct_music_appmsg(title, singer, music_url, thumb_url, "netease")
                        reply.type = ReplyType.APP
                        reply.content = appmsg
                    else:
                        music_path = self.download_music(music_url, "netease")
                        if music_path:
                            reply.type = ReplyType.VOICE
                            reply.content = music_path
                        else:
                            reply.content = "音乐文件下载失败，请稍后重试"
                else:
                    reply.content = f"随机{'点歌' if content.strip() == '随机点歌' else '听歌'}失败，请稍后重试"
            else:
                reply.content = f"随机{'点歌' if content.strip() == '随机点歌' else '听歌'}失败，请稍后重试"
        except Exception as e:
            logger.error(f"[SearchMusic] 随机{'点歌' if content.strip() == '随机点歌' else '听歌'}错误: {e}")
            reply.content = f"随机{'点歌' if content.strip() == '随机点歌' else '听歌'}失败，请稍后重试"

    def handle_platform_music(self, content, reply):
        platforms = {
            "酷狗": "kugou",
            "网易": "netease",
            "汽水": "qishui"
        }
        for platform_prefix, platform in platforms.items():
            if content.startswith(f"{platform_prefix}点歌 ") or content.startswith(f"{platform_prefix}听歌 "):
                song_name, song_number = self.parse_song_command(content, 5)
                if not song_name:
                    reply.content = "请输入要搜索的歌曲名称"
                    return

                url = self.get_platform_url(platform, song_name, song_number)
                try:
                    response = requests.get(url, timeout=10)
                    if content.startswith(f"{platform_prefix}点歌 "):
                        self.handle_platform_song_info(response, reply, platform, song_name, song_number)
                    else:
                        self.handle_platform_song_download(response, reply, platform)
                except Exception as e:
                    logger.error(f"[SearchMusic] {platform_prefix}{'点歌' if content.startswith(f'{platform_prefix}点歌 ') else '听歌'}错误: {e}")
                    reply.content = "获取失败，请稍后重试"
                break

    def get_platform_url(self, platform, song_name, song_number):
        urls = {
            "kugou": f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={song_name}&n={song_number}",
            "netease": f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={song_name}&n={song_number}",
            "qishui": f"https://hhlqilongzhu.cn/api/dg_qishuimusic.php?msg={song_name}&n={song_number}"
        }
        return urls.get(platform, "")

    def handle_platform_song_info(self, response, reply, platform, song_name, song_number):
        content = response.text
        song_info = content.split('\n')
        if len(song_info) >= 4:
            title = song_info[1].replace("歌名：", "").strip()
            singer = song_info[2].replace("歌手：", "").strip()
            detail_url = song_info[3].replace("歌曲详情页：", "").strip()
            music_url = song_info[4].replace("播放链接：", "").strip()

            thumb_url = self.extract_cover_from_response(content)
            if not thumb_url:
                thumb_url = self.get_music_cover(platform, detail_url, title, singer)

            appmsg = self.construct_music_appmsg(title, singer, music_url, thumb_url, platform)
            reply.type = ReplyType.APP
            reply.content = appmsg
        else:
            reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

    def handle_platform_song_download(self, response, reply, platform):
        content = response.text
        song_info = content.split('\n')
        if len(song_info) >= 4:
            music_url = song_info[4].strip()
            if "播放链接：" in music_url:
                music_url = music_url.split("播放链接：")[1].strip()

            music_path = self.download_music(music_url, platform)
            if music_path:
                reply.type = ReplyType.VOICE
                reply.content = music_path
            else:
                reply.content = "音乐文件下载失败，请稍后重试"
        else:
            reply.content = "未找到该歌曲，请确认歌名和序号是否正确"

    def parse_song_command(self, content, command_length):
        """
        解析歌曲命令，返回歌曲名称和序号。
        如果用户没有输入序号，默认使用序号1。

        :param content: 用户输入的完整命令
        :param command_length: 命令的长度（如 "酷狗点歌 " 的长度为5）
        :return: (song_name, song_number)
        """
        song_name = content[command_length:].strip()  # 去除多余空格
        if not song_name:
            return None, None

        # 检查是否包含序号，如果不包含，默认使用序号1
        params = song_name.split()
        if len(params) == 1:
            song_name = params[0]
            song_number = "1"  # 默认使用序号1
        elif len(params) == 2 and params[1].isdigit():
            song_name, song_number = params
        else:
            return None, None

        return song_name, song_number

    def get_help_text(self, **kwargs):
        return (
            " 音乐搜索和播放功能：\n\n"
            "1. 酷狗音乐：\n"
            "   - 搜索歌单：发送「酷狗点歌 歌曲名称」\n"
            "   - 音乐卡片：发送「酷狗点歌 歌曲名称 序号」\n"
            "   - 语音播放：发送「酷狗听歌 歌曲名称 序号」\n"
            "2. 网易音乐：\n"
            "   - 搜索歌单：发送「网易点歌 歌曲名称」\n"
            "   - 音乐卡片：发送「网易点歌 歌曲名称 序号」\n"
            "   - 语音播放：发送「网易听歌 歌曲名称 序号」\n"
            "3. 汽水音乐：\n"
            "   - 搜索歌单：发送「汽水点歌 歌曲名称」\n"
            "   - 音乐卡片：发送「汽水点歌 歌曲名称 序号」\n"
            "   - 语音播放：发送「汽水听歌 歌曲名称 序号」\n"
            "4. 随机点歌：发送「随机点歌」获取随机音乐卡片\n"
            "5. 随机听歌：发送「随机听歌」获取随机语音播放\n"
            "注：序号在搜索结果中获取"
        )
