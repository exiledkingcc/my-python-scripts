#!/usr/bin/env python3

import sys
import json
import requests
from bs4 import BeautifulSoup


def parse_link(html):
    soup = BeautifulSoup(html, "lxml")
    a = soup.find_all("a")
    for i in a:
        if "中华人民共和国县以上行政区划代码" in i.text:
            return i.get("href")
    return None


def get_and_parse_link(link):
    r = requests.get(link)
    text = r.text
    p = text.find("window.location.href=")
    if p > 0:
        p = text.find("\"", p)
        p += 1
        q = text.find("\"", p)
        real_link = text[p:q]
    else:
        real_link = parse_link(text)
    if not real_link.startswith("http"):
        real_link = "http://www.mca.gov.cn" + real_link
    return real_link


def get_and_parse_data(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table")
    trs = table.find_all("tr")
    r = []
    for tr in trs:
        p = tr.text.strip().split("\n")
        if len(p) != 2:
            continue
        c = p[0].strip()
        if not ord("0") <= ord(c[0]) <= ord("9"):
            continue
        n = p[1].strip()
        r.append((c, n))
    rr = []
    prov = ""
    city = ""
    for i in r:
        code, name = i
        if code.endswith("0000"):
            prov = name
            city = ""
            dist = ""
            name = prov
        elif code.endswith("00"):
            city = name
            dist = ""
            name = prov + city
        else:
            dist = name
            name = prov + city + dist
        rr.append((code, name, prov, city, dist))
    return rr


def write_data(data, fname):
    keys = sorted(data.keys())
    dd = []
    for k in keys:
        v = data[k]
        d = [k]
        d.extend(v)
        dd.append(d)
    with open(fname, "w") as f:
        for d in dd:
            f.write(",".join(d))
            f.write("\n")


def main(script, dblinks, *argv):
    with open(dblinks) as f:
        links = f.readlines()
    links = [lk.split(",")[0].strip() for lk in links]
    links = [get_and_parse_link(lk) for lk in links]
    code_name = {}
    name_code = {}
    names = {}
    for lk in links:
        print("processing", lk)
        data = get_and_parse_data(lk)
        for dd in data:
            code, name, prov, city, dist = dd

            nm = code_name.get(code, set())
            nm.add(name)
            code_name[code] = nm

            cd = name_code.get(name, set())
            cd.add(code)
            name_code[name] = cd

            p = names.get(prov, {})
            c = p.get(city, {})
            c[dist] = code
            p[city] = c
            names[prov] = p
    # write_data(code_name, "id_code.txt")
    # write_data(name_code, "id_name.txt")
    for k in code_name:
        v = list(code_name[k])
        code_name[k] = v
    for k in name_code:
        v = list(name_code[k])
        name_code[k] = v
    json.dump(code_name, open("id_code.json", "w"))
    json.dump(name_code, open("id_name.json", "w"))
    json.dump(names, open("id_relation.json", "w"))


if __name__ == '__main__':
    main(*sys.argv)
