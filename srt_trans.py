#!/usr/bin/env python
# coding: UTF-8
#
# this program is designed to translate to chinese only.
from __future__ import unicode_literals
import sys
import re
import threading
import logging
logging.basicConfig(level=logging.INFO)

import json
from textwrap import wrap
try:
    import urllib2 as request
    from urllib import quote
except:
    from urllib import request
    from urllib.parse import quote


class Translator:
    # ----------------------------------------------------------------------------
    # "THE BEER-WARE LICENSE" (Revision 42):
    # <terry.yinzhe@gmail.com> wrote this file. As long as you retain this notice you
    # can do whatever you want with this stuff. If we meet some day, and you think
    # this stuff is worth it, you can buy me a beer in return to Terry Yin.
    #
    # The idea of this is borrowed from <mort.yao@gmail.com>'s brilliant work
    #    https://github.com/soimort/google-translate-cli
    # He uses "THE BEER-WARE LICENSE". That's why I use it too. So you can buy him a
    # beer too.
    # ----------------------------------------------------------------------------
    string_pattern = r"\"(([^\"\\]|\\.)*)\""
    match_string = re.compile(r"\,?\["
                              + string_pattern + r"\,"
                              + string_pattern + r"\,"
                              + string_pattern + r"\,"
                              + string_pattern
                              + r"\]")

    def __init__(self, to_lang, from_lang='auto'):
        self.from_lang = from_lang
        self.to_lang = to_lang

    def translate(self, source):
        self.source_list = wrap(source, 1000, replace_whitespace=False)
        return ' '.join(self._get_translation_from_google(s) for s in self.source_list)

    def _get_translation_from_google(self, source):
        json5 = self._get_json5_from_google(source)
        return self._unescape(self._get_translation_from_json5(json5))

    def _get_translation_from_json5(self, content):
        result = ""
        pos = 2
        while True:
            m = self.match_string.match(content, pos)
            if not m:
                break
            result += m.group(1)
            pos = m.end()
        return result

    def _get_json5_from_google(self, source):
        escaped_source = quote(source.encode('UTF-8'), '')
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.168 Safari/535.19'}
        req = request.Request(
            url="http://translate.google.cn/translate_a/t?client=t&ie=UTF-8&oe=UTF-8&sl=%s&tl=%s&text=%s" % (self.from_lang, self.to_lang, escaped_source),
            headers=headers)
        r = request.urlopen(req)
        return r.read().decode('utf-8')

    def _unescape(self, text):
        return json.loads('"%s"' % text)

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
        except:
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
                try:
                    line = ifile.readline().decode('cp1252')
                except:
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

    n_of_t = 10
    semaphor = threading.Semaphore(n_of_t)

    def do_translate(job, result, index, semaphor):
        logging.info('translating %s - %s' % (index, index + n))
        result[index:index+n] = trans.translate('\r\n'.join(job[index:index+n])).splitlines()
        semaphor.release()

    n = 10
    i = 0
    while i < len(job):
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
