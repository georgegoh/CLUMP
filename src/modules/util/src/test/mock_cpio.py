#!/bin/env python
import sys
# def main():
#     """We take 1 argument, which tells us if we should error, and what the error code should be"""

class MockCpio:
    def __init__(self):
        self.args = sys.argv
        self.errornum = 0
    def run(self):
        print ''.join(["number of args ", str(len(self.args))])
        if len(self.args) == 2:
            self.errornum = self.args[1]
            sys.exit(self.errornum)
        #default error to 1
        else:
            sys.exit(2)
        
    def usage(self):
        print "Usage: %s <num>  where num is the exit value" % (self.args[0])
        

    
if __name__ == '__main__':
    mock_cpio = MockCpio()
    mock_cpio.run()
