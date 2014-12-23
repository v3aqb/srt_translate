#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#
# this program is designed to translate to chinese only.
from __future__ import unicode_literals
import sys
import re
import threading
from translate import Translator
import logging
logging.basicConfig(level=logging.INFO)

trans = Translator('zh')

if len(sys.argv) < 2:
    fname = raw_input('file name?: ')
else:
    fname = sys.argv[1]

fsplit = fname.split('.')
fsplit[-2] = 'chn'
oname = '.'.join(fsplit)

ifile = open(fname, 'rb')
output = []
job = []

while 1:
    line = ifile.readline()
    if not line:
        break
    line = line.replace(b'\xef\xbb\xbf', b'').decode('UTF-8')
    if not line.strip():
        output.append('\r\n')
    elif line.strip().isdigit():
        output.append(line)
    elif ' --> ' in line:
        output.append(line)
    else:
        script = re.sub(r'<[^<]+>', '', line.strip())
        append = ''
        while not script.endswith(('.', '?', ')', '=', ':')):
            line = ifile.readline().decode('UTF-8')
            if not line:
                break
            if not line.strip():
                append += '\r\n'
                break
            elif line.strip().isdigit():
                append += line
                break
            else:
                script += ' '
                script += re.sub(r'<[^<]+>', '', line.strip())
        output.append(1)
        job.append(script)

        output.append('\r\n')
        output.append(append)

result = [''] * len(job)

semaphor = threading.Semaphore(10)


def do_translate(job, result, index, semaphor):
    logging.info('translating %s' % job[index])
    result[index] = trans.translate(job[index])
    logging.info('result %s' % result[index])
    semaphor.release()

for i in range(len(job)):
    semaphor.acquire()
    threading.Thread(target=do_translate, args=(job, result, i, semaphor)).start()

job_iter = iter(job)
result_iter = iter(result)

ofile = open(oname, 'wb')
ofile.write(b'\xef\xbb\xbf')

for item in output:
    if item == 1:
        ofile.write(next(result_iter).encode('UTF-8'))
        # ofile.write(b'\r\n')
        # ofile.write(job_iter.next().encode('UTF-8'))
    else:
        ofile.write(item.encode('UTF-8'))

ofile.close()
