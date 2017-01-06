#!/usr/bin/env python3

import sys
import functools
import traceback
import json
import requests
from bs4 import BeautifulSoup

jd_sess = requests.session()
jd_sess.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/55.0.2883.87 Chrome/55.0.2883.87 Safari/537.36"})


def safe_run(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err = ["\n\x1b[31m"] + traceback.format_exception(Exception, e, e.__traceback__) + ["\x1b[0m"]
            print("".join(err), file=sys.stderr)
            return None
    return wrapper


def fetch_openwrt_devices():
    url = "https://wiki.openwrt.org/toh/start"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table", attrs={"class": "dataplugin_table"})
    trs = table.find_all("tr")
    devices = []
    for tr in trs:
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        brand = tds[1].string.strip()
        model = tds[2].string.strip()
        devices.append((brand, model))
    return devices


@safe_run
def search_jd_items(keyword):
    params = {
        "keyword": keyword
    }
    url = "https://search.jd.com/Search"
    r = jd_sess.get(url, params=params)
    html = str(r.content, "utf-8")
    soup = BeautifulSoup(html, "lxml")
    goods = soup.find("div", attrs={"id": "J_goodsList"})
    if not goods:
        return None

    ul = goods.find("ul")
    lis = ul.find_all("li")
    jd_items = []
    for li in lis[:3]:
        price = li.find("div", attrs={"class": "p-price"}).get_text(strip=True)
        pname = li.find("div", attrs={"class": "p-name"}).find("a")
        name = pname.get("title")
        url = pname.get("href")
        comments = li.find("div", attrs={"class": "p-commit"}).find("a").string
        jd_items.append({
            "price": price,
            "name": name,
            "url": url,
            "comments": comments,
        })
    return jd_items


def main(script, *argv):
    all_data = {}
    devices = fetch_openwrt_devices()
    for dev in devices:
        brand, name = dev
        print(brand, name)
        keyword = "{} {}".format(brand, name)
        jd_items = search_jd_items(keyword)
        if not jd_items:
            print("Not found in jd.com")
        else:
            for item in jd_items:
                print("{price} {name}".format(**item))
            if brand not in all_data:
                all_data[brand] = {}
            all_data[brand][name] = jd_items
        print()
    json.dump(all_data, open("openwrt.json", "w"), ensure_ascii=False)


if __name__ == '__main__':
    main(*sys.argv)
