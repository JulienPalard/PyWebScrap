#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
from PyQt4 import QtCore, QtGui, QtWebKit


class WebScrapper(QtGui.QMainWindow):
    """
    WebScrapper
    ===========

    Download, render and expose the DOM of a webpage to you.
    You can query the DOM using QT functions :

     * http://doc.qt.nokia.com/4.6/qwebframe.html
     * http://doc.qt.nokia.com/4.6/qwebelement.html

    Calling Convention
    ==================

    scrap.py use a postfix calling convention.
    So if you want to call findFirstElement(h1) you should write :
    h1 findFirstElement

    To call styleProperty("background-image", ComputedStyle) you should use :
    background-image ComputedStyle styleProperty

     * Every function applies on the result of the preceding function
     * If the preceding function has returned an array, following functions are
       applied for each elements of the returned array
     * If you put a ; you break the command and starts a new one
       from the QWebFrame

    Examples
    ========
    # Simply fetch the plain text value of the first h1 on my page :
    $ scrap.py http://www.mandark.fr h1 findFirstElement toPlainText
    Julien Palard

    # There is no h2 inside of the h1 !
    $ scrap.py http://www.mandark.fr h1 findFirstElement toPlainText \
                                     h2 findFirstElement toPlainText
    Julien Palard

    # A list is returned json encoded :
    $ scrap.py http://www.mandark.fr h1 findFirstElement toPlainText \; \
                                     h2 findFirstElement toPlainText
    ["Julien Palard", "CTO at meltynetwork.fr"]

    # I don't have a background image on my personal website ...
    $ scrap.py http://www.mandark.fr/ 'body' findFirstElement background-image \
                             ComputedStyle styleProperty
    "none"

    # But I have two <script>, so this will return an array of two strings :
    scrap.py http://www.mandark.fr script findAllElements toPlainText
    ["\nvar gaJsHost = ((\"https:\" == document.location.protocol) ? \"https:...

    """

    def __init__(self, site, instruction_set):
        self.app = QtGui.QApplication([])
        self.site = site
        self.instruction_set = instruction_set
        QtGui.QWidget.__init__(self)
        self.webView = QtWebKit.QWebView(QtGui.QWidget(self))
        QtCore.QObject.connect(self.webView,QtCore.SIGNAL("loadFinished(bool)"), self.loadFinished)
        self.webView.load(QtCore.QUrl(self.site))
        self.app.exec_()

    def dump(self, el):
        if isinstance(el, QtCore.QString):
            return unicode(el.toUtf8(), "utf-8")
        if isinstance(el, QtWebKit.QWebElementCollection):
            return self.dump(el.toList())
        if isinstance(el, list):
            return [self.dump(i) for i in el]
        return el

    def cascade(self, el, todo):
        origin = el
        arguments = []
        for idx, item in enumerate(todo):
            if hasattr(el, item):
                try:
                    target = getattr(el, item)
                    if callable(target):
                        el = target(*arguments)
                        if isinstance(el, QtWebKit.QWebElementCollection):
                            output = []
                            for i in el.toList():
                                 output.append(self.cascade(i, todo[idx + 1:]))
                            return output
                        arguments = []
                    else:
                        arguments.append(getattr(el, item))
                except Exception as ex:
                    print ex, "while calling", item, "with", arguments
                    self.close()
                    return
            else:
                arguments.append(item)
        return self.dump(el)

    def get_instructions(self):
        instruction_set = [[]]
        for i in self.instruction_set:
            if i == ';':
                instruction_set.append([])
            else:
                instruction_set[-1].append(i)
        return instruction_set

    def loadFinished(self):
        try:
            output = []
            for instructions in self.get_instructions():
                output.append(self.cascade(self.webView.page().currentFrame(),
                                           instructions))
            if len(output) == 1:
                self.result = output[0]
            else:
                self.result = json.dumps(output)
        finally:
            self.close()

if __name__ == "__main__":
    scrapper = WebScrapper(sys.argv[1], sys.argv[2:])
    print scrapper.result

