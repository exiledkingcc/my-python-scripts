# my-python-scripts
my python scripts collection


### fzdm.py

#### description:
从[风之动漫](http://www.fzdm.com)上爬漫画，并生成html链接

#### usage:
```bash
# list all comics with its index
fzdm.py list
# find {name} with its index
fzdm.py find {name}
# fetch comic which index is {index} into {dirname}
fzdm.py fetch {index} {dirname}
# build html links
fzdm.py build {dirname}
# clean html links
fzdm.py clean {dirname}
```
#### example:
```bash
$ ./fzdm.py find 柯南
142  名侦探柯南
$ ./fzdm.py find 天下
15   天上天下
74   王者天下
$ ./fzdm.py fetch 74 王者天下 2>err.log
....
$ ./fzdm.py build 王者天下
```
然后`王者天下`文件夹下会生成`index.html`，可在浏览器中打开看漫画。


### cckill.py

#### description:
kill by name, like killall

### usage:
`cckill.py [options] name`


### id_db.py

#### description:
生成身份证前六位与地区对应关系，数据来源：[中华人民共和国民政部](http://www.mca.gov.cn)

`id_links.txt`里面是历年数据。

包含全部新旧数据，不过没有标注时间。

结果存储在`id_code.json, id_name.json, id_relation.json`里面。

#### usage:
`id_db.py id_links.txt`


### cclog.py

#### description:
输出彩色日志


### seek_openwrt.py

#### description:
获取支持openwrt的设备列表，

然后到jd.com上搜索路由器的价格，链接，评价数，（只取前三个）

结果会写到`openwrt.json`文件中


