#!/usr/bin/env python3

import sys
import os


def get_pid(item):
    return item.split()[1]


def get_list(cmd):
    ret = os.popen("ps -ef | grep {}".format(cmd)).read()
    ret = ret.split("\n")
    ret = [x for x in ret if len(x) > 0 and
           "cckill.py" not in x and "grep {}".format(cmd) not in x]
    ret = [(get_pid(x), x) for x in ret]
    return ret


def kill(pids, opt=""):
    pidstr = " ".join(pids)
    os.system("kill {} {}".format(opt, pidstr))


def main(script, *argv):
    if len(argv) == 1:
        opt = ""
        names = [argv[0]]
    elif len(argv) >= 2:
        opt = argv[0]
        names = argv[1:]

    ps = []
    for n in names:
        ps.extend(get_list(n))

    if len(ps) == 0:
        print("no process found.")
        return

    for i in range(len(ps)):
        p = ps[i]
        print("[{}] {}".format(i, p[1]))

    n = input("which do you want to kill? (a for all):")

    if n == "":
        return
    elif n == "a":
        kill([x[0] for x in ps], opt)
    else:
        try:
            idx = int(n)
            kill([ps[idx][0]], opt)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main(*sys.argv)
