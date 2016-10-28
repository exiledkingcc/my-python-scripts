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
cckill.py [-2|-9] name
