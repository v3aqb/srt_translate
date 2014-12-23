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
    if sys.version_info < (3, 0):
        fname = raw_input('file name?: ')
    else:
        fname = input('file name?: ')
    fnames = [fname]
else:
    fnames = sys.argv[1:]

for fname in fnames:
    logging.info('translating %s' % fname)
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
        try:
            line = line.replace(b'\xef\xbb\xbf', b'').decode('cp1252')
            co = 'cp1252'
        except:
            line = line.replace(b'\xef\xbb\xbf', b'').decode('UTF-8')
            co = 'UTF-8'
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
                line = ifile.readline().decode(co)
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

    n_of_t = 10
    semaphor = threading.Semaphore(n_of_t)


    def do_translate(job, result, index, semaphor):
        logging.info('translating %s - %s' % (index, index + n))
        result[index:index+n] = trans.translate('\r\n'.join(job[index:index+n])).splitlines()
        semaphor.release()

    n = 10
    i = 0
    while i <= len(job):
        semaphor.acquire()
        threading.Thread(target=do_translate, args=(job, result, i, semaphor)).start()
        # do_translate(job, result, i, semaphor)
        i += n

    for i in range(n_of_t):
        semaphor.acquire()

    job_iter = iter(job)
    result_iter = iter(result)

    ofile = open(oname, 'wb')
    ofile.write(b'\xef\xbb\xbf')

    for item in output:
        if item == 1:
            ofile.write(next(result_iter).encode('UTF-8'))
            ofile.write(b'\r\n')
            ofile.write(next(job_iter).encode('UTF-8'))
        else:
            ofile.write(item.encode('UTF-8'))

    ofile.close()
