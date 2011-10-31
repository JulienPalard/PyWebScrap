#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
import json
import urlparse
from PyQt4 import QtCore, QtGui, QtWebKit, QtNetwork
from collections import defaultdict, namedtuple
from datetime import datetime

Progress = namedtuple('Progress', ['date', 'bytesReceived', 'totalBytes'])

class InfiniteArray:
    def __init__(self, values=None):
        self.chunks = {}
        self.min = 0
        self.max = 0
        if values is not None:
            for key, value in enumerate(values):
                self[key] = value

    def get_chunk(self, index):
        if index not in self.chunks:
            self.chunks[index] = [0 for i in xrange(4096)]
        return self.chunks[index]

    def __getitem__(self, index):
        return self.get_chunk(index / 4096)[index % 4096]

    def __setitem__(self, index, value):
        self.min = min(self.min, index)
        self.max = max(self.max, index)
        self.get_chunk(index / 4096)[index % 4096] = value

    def toList(self):
        return [self[x] for x in range(self.min, self.max)]

def totalSeconds(delta):
    return (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10**6) / 10**6

def toUnicode(obj):
    return unicode(obj.toString().toUtf8(), 'utf-8')

class networkReplyStater():
    def __init__(self, networkReply):
        QtCore.QObject.connect(networkReply,
                               QtCore.SIGNAL("downloadProgress(qint64, qint64)"),
                               self.downloadProgress)


    def downloadProgress(self, bytesReceived, totalBytes):
        self.totalBytes = totalBytes


class loggingNam(QtNetwork.QNetworkAccessManager):
    contentTypeHeader = QtNetwork.QNetworkRequest.ContentTypeHeader

    def __init__(self, stats):
        super(loggingNam, self).__init__()
        QtCore.QObject.connect(self, QtCore.SIGNAL("finished(QNetworkReply *)"),
                               self.finished)
        stats['by_content_type'] = defaultdict(list)
        stats['requests'] = {}
        stats['start'] = datetime.now()
        self.stats = stats

    def createRequest(self, op, req, outgoingData):
        stats = {'start': totalSeconds(datetime.now() - self.stats['start']),
                 'headers': {}}
        self.stats['requests'][toUnicode(req.url())] = stats
        networkReply = super(loggingNam, self).createRequest(op, req,
                                                             outgoingData)
        stats['network'] = networkReplyStater(networkReply)
        return networkReply

    def finished(self, response):
        url = toUnicode(response.request().url())
        stats = self.stats['requests'][url]
        stats['totalBytes'] = stats['network'].totalBytes
        del stats['network']
        content_type = toUnicode(response.header(self.contentTypeHeader))
        self.stats['by_content_type'][content_type].append(url)
        stats['finished'] = totalSeconds(datetime.now() - self.stats['start'])
        stats['duration'] = stats['finished'] - stats['start']
        for header in response.rawHeaderList():
            stats['headers'][unicode(header.data())] = response.rawHeader(header).data()


class WebBrowserWithStatistics(QtGui.QMainWindow):
    def __init__(self, site):
        self.app = QtGui.QApplication([])
        QtGui.QWidget.__init__(self)
        self.stats = {}
        self.webView = QtWebKit.QWebView(QtGui.QWidget(self))
        self.nam = loggingNam(self.stats)
        self.webView.page().setNetworkAccessManager(self.nam)
        QtCore.QObject.connect(self.webView,QtCore.SIGNAL("loadFinished(bool)"), self.loadFinished)
        self.webView.load(QtCore.QUrl(site))
        self.app.exec_()

    def loadFinished(self):
        del self.stats['start']
        self.webView.stop()
        self.close()

if __name__ == "__main__":
    browser = WebBrowserWithStatistics(sys.argv[1])
    print json.dumps(browser.stats)
