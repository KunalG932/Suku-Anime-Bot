import asyncio
from aiohttp import ClientSession
from os import path as ospath
from aiofiles import open as aiopen
from aiofiles.os import path as aiopath, remove as aioremove, mkdir
from torrentp import TorrentDownloader
from bot import LOGS
from bot.core.func_utils import handle_logs

class TorDownloader:
    def __init__(self, path="."):
        self.__downdir = path
        self.__torpath = "torrents/"
        self.__retry_limit = 3  # Retry limit for failed downloads
    
    @handle_logs
    async def download(self, torrent, name=None):
        if torrent.startswith("magnet:"):
            torp = TorrentDownloader(torrent, self.__downdir)
            await torp.start_download()
            return ospath.join(self.__downdir, name or "downloaded_torrent")
        elif torfile := await self.get_torfile(torrent):
            torp = TorrentDownloader(torfile, self.__downdir)
            await torp.start_download()
            await aioremove(torfile)
            return ospath.join(self.__downdir, torp._torrent_info._info.name())
    
    @handle_logs
    async def get_torfile(self, url):
        if not await aiopath.isdir(self.__torpath):
            await mkdir(self.__torpath)
        
        tor_name = url.split('/')[-1]
        des_dir = ospath.join(self.__torpath, tor_name)
        retries = 0
        
        while retries < self.__retry_limit:
            async with ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            async with aiopen(des_dir, 'wb') as file:
                                async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                                    await file.write(chunk)
                            return des_dir
                except asyncio.TimeoutError:
                    retries += 1
                    LOGS.warning(f"Timeout occurred, retrying {retries}/{self.__retry_limit}...")
                except Exception as e:
                    LOGS.error(f"Error downloading torrent file: {e}")
                    retries += 1
        return None
