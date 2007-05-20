#!/usr/bin/python

class BIGone:
    def __init__(self):
        self.var1 = 'Hello'

    def cfun(self):
        self.newvar = "Surprise"


class Upper(BIGone):
    def ufun(self):
        print "var1 = %s" % self.var1
        print "newvar = %s" % self.newvar


app = Upper()
app.cfun()
app.ufun()
