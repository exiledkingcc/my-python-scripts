#!/usr/bin/env python3

import sys
import logging

from bs4 import BeautifulSoup
import requests

import cclog

log = logging.getLogger(__name__)


class Req:
    SESSION = requests.session()

    @staticmethod
    def get(*args, **kwargs):
        return Req.SESSION.get(*args, **kwargs)

    @staticmethod
    def post(*args, **kwargs):
        return Req.SESSION.post(*args, **kwargs)


class Subtitle:
    PLUGINS = []

    @staticmethod
    def download(name, episode):
        sub = None
        for plgcls in Subtitle.PLUGINS:
            plg = plgcls()
            sub = plg.search(name, episode)
            if sub:
                break
        if not sub:
            log.warning("not found...")
            return

        name, url = sub
        log.info("downloading... %s", name)
        r = Req.get(url, stream=True)
        if not r.ok:
            log.error("download error: %s", r.status)
        dsize = 0
        with open(name, "wb") as f:
            for block in r.iter_content(4096):
                f.write(block)
                dsize += len(block)
                log.info("downloaded %d bytes...", dsize)
        log.info("%s saved!", name)

    @staticmethod
    def plugin(cls):
        class Wrapper:
            def __init__(self, *args, **kwargs):
                self.wrapped = cls(*args, **kwargs)
            def __getattr__(self, name):
                return getattr(self.wrapped, name)
        if Wrapper not in Subtitle.PLUGINS:
            Subtitle.PLUGINS.append(Wrapper)
        return Wrapper


@Subtitle.plugin
class ZimukuPlugin:
    URL = "http://www.zimuku.net"
    def get_url(self, url):
        return "{}{}".format(self.URL, url)

    def search_name(self, name):
        log.info("%s", name)
        searchurl = self.get_url("/search")
        r = Req.get(searchurl, params={"q": name})
        soup = BeautifulSoup(r.text, "lxml")
        div = soup.find("div", attrs={"class": "title"})
        subhref = div.find("a").get("href")
        suburl = self.get_url(subhref)
        log.info("suburl: %s", suburl)
        r = Req.get(suburl)
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", attrs={"id": "subtb"})
        trs = table.find("tbody").find_all("tr")
        subs = []
        for tr in trs:
            td = tr.find("td", attrs={"class": "first"})
            a = td.find("a")
            name = a.text
            href = a.get("href")
            url = self.get_url(href)
            subs.append((name, url))
        return subs

    def get_best_match(self, subs, episode):
        def match(name, ep):
            m1 = "第{}集".format(episode)
            m2 = "E{}".format(episode)
            p = name.find(m1)
            if p < 0:
                return 0
            q = name.find(m2, p)
            if q < 0:
                return 1
            return 2

        log.info("episode: %s", episode)
        s = None
        m = 0
        for sub in subs:
            name = sub[0]
            mm = match(name, episode)
            if mm > m:
                m = mm
                s = sub
        return s

    def get_sub_url(self, detail_url):
        log.info("%s", detail_url)
        r = Req.get(detail_url)
        soup = BeautifulSoup(r.text, "lxml")
        ul = soup.find("ul", attrs={"class": "subinfo"})
        li = ul.find("li", attrs={"class": "dlsub"})
        a = li.find("a")
        return self.get_url(a.get("href"))

    def get_sub_name(self, name):
        p = 0
        for i in range(-1, -len(name), -1):
            if ord(name[i]) > 255:
                p = i
                break
        p += 1
        if name[p] in [")"]:
            p += 1
        return name[p:]

    def search(self, name, episode):
        subs = self.search_name(name)
        sub = self.get_best_match(subs, episode)
        if not sub:
            return None

        name, url = sub
        name = self.get_sub_name(name)
        url = self.get_sub_url(url)
        return (name, url)


def main(script, name, episode):
    log.info("start...")
    Subtitle.download(name, episode)


if __name__ == '__main__':
    cclog.init(disable=["requests"])
    main(*sys.argv)
