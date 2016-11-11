import os
from urllib2 import urlopen
from collections import defaultdict
from urlparse import unquote
import json
import logging

from collections import defaultdict 
from video import Video

log = logging.getLogger(__name__)

class PytubeError(Exception):
    pass

class AgeRestricted(Exception):
    pass

class Pytube(object):
    def __init__(self, url):
        self.url = url

    def get_video_data(self):
        """Gets the page and extracts out the video data."""
        # Reset the filename incase it was previously set.
        self.title = None
        response = urlopen(self.url)
        if not response:
            raise PytubeError("Unable to open url: {0}".format(self.url))

        html = response.read()
        if isinstance(html, str):
            restriction_pattern = "og:restrictions:age"
        else:
            restriction_pattern = bytes("og:restrictions:age", "utf-8")

        if restriction_pattern in html:
            raise AgeRestricted("Age restricted video. Unable to download "
                                "without being signed in.")

        # Extract out the json data from the html response body.
        json_object = self._get_json_data(html)

        # Here we decode the stream map and bundle it into the json object. We
        # do this just so we just can return one object for the video data.
        encoded_stream_map = json_object.get("args", {}).get(
            "url_encoded_fmt_stream_map")
        json_object["args"]["stream_map"] = self._parse_stream_map(
            encoded_stream_map)
        return json_object

    def _get_json_data(self, html):
        """Extract the json out from the html.
        :param str html:
            The raw html of the page.
        """
        # 18 represents the length of "ytplayer.config = ".
        if isinstance(html, str):
            json_start_pattern = "ytplayer.config = "
        else:
            json_start_pattern = bytes("ytplayer.config = ", "utf-8")
        pattern_idx = html.find(json_start_pattern)
        # In case video is unable to play
        if(pattern_idx == -1):
            raise PytubeError("Unable to find start pattern.")
        start = pattern_idx + 18
        html = html[start:]

        offset = self._get_json_offset(html)
        if not offset:
            raise PytubeError("Unable to extract json.")
        if isinstance(html, str):
            json_content = json.loads(html[:offset])
        else:
            json_content = json.loads(html[:offset].decode("utf-8"))

        return json_content

    def _get_json_offset(self, html):
        """Find where the json object starts.
        :param str html:
            The raw html of the YouTube page.
        """
        unmatched_brackets_num = 0
        index = 1
        for i, ch in enumerate(html):
            if isinstance(ch, int):
                ch = chr(ch)
            if ch == "{":
                unmatched_brackets_num += 1
            elif ch == "}":
                unmatched_brackets_num -= 1
                if unmatched_brackets_num == 0:
                    break
        else:
            raise PytubeError("Unable to determine json offset.")
        return index + i

    def _parse_stream_map(self, blob):
        """A modified version of `urlparse.parse_qs` that's able to decode
        YouTube's stream map.
        :param str blob:
            An encoded blob of text containing the stream map data.
        """
        dct = defaultdict(list)

        # Split the comma separated videos.
        videos = blob.split(",")

        # Unquote the characters and split to parameters.
        videos = [video.split("&") for video in videos]

        # Split at the equals sign so we can break this key value pairs and
        # toss it into a dictionary.
        for video in videos:
            for kv in video:
                key, value = kv.split("=")
                dct[key].append(unquote(value))
        log.debug("decoded stream map: %s", dct)
        return dct
    
    def download(self, filename, path=None):
        if not path:
            path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resp = self.get_video_data()
        url_data = resp['args']['stream_map']
        d = defaultdict(object)
        urls = url_data['url']
        url = urls[0]
        v = Video(url, filename)
        v.download(path)

url = 'https://www.youtube.com/watch?v=hDS4FVg7kio'

a = Pytube(url)

a.download('video1.mp4')


