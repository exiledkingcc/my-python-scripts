#!/usr/bin/env python3

import sys, os
import requests
from html.parser import HTMLParser
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

FZDM_URL = "http://manhua.fzdm.com"

class ImgURLParser(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self._url = url
        self._img_url = None
        self._next = None

    def img_url(self):
        return self._img_url

    def next_url(self):
        return self._next if self._next != self._url else None

    def _get_id(self, attrs):
        return _get_attr(attrs, "id")

    def _get_src(self, attrs):
        return _get_attr(attrs, "src")

    def _get_href(self, attrs):
        return _get_attr(attrs, "href")

    def handle_starttag(self, tag, attrs):
        if tag == "img" and self._get_id(attrs) == "mhpic":
            self._img_url = self._get_src(attrs)
        elif tag == "a" and self._get_id(attrs) == "mhona":
            self._next = self._get_href(attrs)

class EpisodeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._start = False
        self._episodes = []

    def episodes(self):
        return self._episodes

    def _get_class(self, attrs):
        return _get_attr(attrs, "class")

    def _get_href(self, attrs):
        return _get_attr(attrs, "href")

    def _get_title(self, attrs):
        return _get_attr(attrs, "title")

    def handle_starttag(self, tag, attrs):
        if tag == "li" and self._get_class(attrs) == "pure-u-1-2 pure-u-lg-1-4":
            self._start = True
        elif tag == "a" and self._start:
            href = self._get_href(attrs)
            title = self._get_title(attrs)
            self._episodes.append((title, href))
            self._start = False

class ListParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._start = False
        self._comics = []

    def comics(self):
        return self._comics

    def _get_class(self, attrs):
        return _get_attr(attrs, "class")

    def _get_href(self, attrs):
        return _get_attr(attrs, "href")

    def _get_title(self, attrs):
        return _get_attr(attrs, "title")

    def handle_starttag(self, tag, attrs):
        if tag == "div" and self._get_class(attrs) == "round":
            self._start = True
        elif tag == "a" and self._start:
            href = self._get_href(attrs)
            title = self._get_title(attrs)
            self._comics.append((title.strip("漫画"), href.strip("/")))
            self._start = False


def _get_attr(attrs, att):
    for attr in attrs:
        if attr[0] == att:
            return attr[1]
    return None


_sess = requests.Session()
_sess.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"})


def parse_img_url(url):
    imgsrcs = []
    u = ""
    while u is not None:
        uu = url + u
        r = _sess.get(uu, verify=False)
        parser = ImgURLParser(u)
        parser.feed(r.text)
        imgurl = parser.img_url()
        u = parser.next_url()
        parser.close()
        imgsrcs.append(imgurl)
    return imgsrcs

def parse_episodes(url):
    r = _sess.get(url, verify=False)
    parser = EpisodeParser()
    parser.feed(r.text)
    episodes = parser.episodes()
    parser.close()
    return episodes

def write_image(fname, content):
    with open(fname, "wb") as f:
        f.write(content)

def store_image(dirname, imgurls):
    done = os.path.join(dirname, ".done")
    if os.path.exists(done):
        print("fetch {} done.".format(dirname))
        return
    xlen = len(imgurls)
    for i in range(xlen):
        url = imgurls[i]
        p = os.path.join(dirname, "{:02}".format(i))
        print("get image {}, url:{} ...".format(p, url), end=" ")
        r = _sess.get(url)
        if r.ok:
            print("done.")
            write_image(p, r.content)
        else:
            print("error!")
            print("\x1b[31mError {}\x1b[0m".format(p), file=sys.stderr)
    open(done, 'a').close()
    print("fetch {} done.".format(dirname))

def fetch(index, dirname=".", *argv):
    url = "{}/{}/".format(FZDM_URL, index)
    episodes = parse_episodes(url)
    episodes.reverse()
    for ep in episodes:
        p = os.path.join(dirname, ep[0])
        if not os.path.exists(p):
            os.mkdir(p)
        u = url + ep[1]
        imgsrcs = parse_img_url(u)
        store_image(p, imgsrcs)

def get_list():
    r = _sess.get(FZDM_URL, verify=False)
    parser = ListParser()
    parser.feed(r.text)
    comics = parser.comics()
    parser.close()
    comics = sorted(comics, key=lambda c: int(c[1]))
    return comics

def list_all():
    comics = get_list()
    for c in comics:
        print("{1:4} {0}".format(*c))

def find(name):
    comics = get_list()
    r = []
    for c in comics:
        if name in c[0]:
            r.append(c)
    if len(r) == 0:
        print("not found!")
    for i in r:
        print("{1:4} {0}".format(*i))


def _build_index(dn):
    _tpl = '<a href="{}/episode.html">{}</a><br><br>'
    dd = os.listdir(dn)
    dd = sorted(dd)
    dd = [_tpl.format(d, d) for d in dd if not d.endswith(".html")]
    ss = "\n".join(dd)
    p = os.path.join(dn, "index.html")
    with open(p, "w") as f:
        f.write(ss)

def _build_episode(dn):
    _tpl = '<p>{}</p><img src="{}"><br><br>'
    dd = os.listdir(dn)
    dd = sorted(dd)
    dd = [_tpl.format(d, d) for d in dd if not "." in d]
    ss = "\n".join(dd)
    dx = os.path.basename(os.path.normpath(dn))
    ss = "<title>{}</title>".format(dx) + ss
    p = os.path.join(dn, "episode.html")
    with open(p, "w") as f:
        f.write(ss)

def build(dirname):
    _build_index(dirname)
    dd = os.listdir(dirname)
    for d in dd:
        if d.endswith(".html"):
            continue
        dx = os.path.join(dirname, d)
        _build_episode(dx)


def clean(dirname):
    for d in os.listdir(dirname):
        p = os.path.join(dirname, d)
        if os.path.isdir(p):
            clean(p)
        elif d in ["index.html", "episode.html"]:
            os.remove(p)

CMDS = {"fetch": fetch,
        "list": list_all,
        "find": find,
        "build": build,
        "clean": clean}

def main(script, cmd, *argv):
    CMDS[cmd](*argv)
    _sess.close()

if __name__ == "__main__":
    main(*sys.argv)
