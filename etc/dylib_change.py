'''In OSX dylib files, replace absolute paths to dependencies with
relative paths'''

import sys
import os
import subprocess
from subprocess import Popen, PIPE

def replacePrefix( filepath, currlib, badprefix, goodprefix ):
    newlib = currlib.replace( badprefix, goodprefix )
    output = subprocess.Popen(['install_name_tool', '-change',
                               currlib, newlib, filepath], stdout=PIPE).communicate()[0]
    return True

def examineFile( fpath, do_replace=False ):
    knownWrong = [('/opt/Ice-3.4/lib/', '3rdparty/ICE/lib/')
                  ,('/somethingelse', 'replacemewith')
                  ]

    print('examining '+fpath);
    output = subprocess.Popen(['otool', '-L', fpath], stdout=PIPE).communicate()[0]
    # otool first prints the filename, so start at the second line
    for line in output.splitlines()[1:]:
        libname = line.strip().partition('.dylib ')[0]+'.dylib'
        # for dylib fpaths, the dylib references often (always?) start
        # with a link to themselves.  Skip those.
        if libname != fpath and libname.startswith('/'):
            # replace a bunch of known problems
            replaced = False
            for tupl in knownWrong:
                if libname.startswith( tupl[0] ):
                    if do_replace:
                        replaced = replacePrefix( fpath, libname, tupl[0], tupl[1] )
                        print 'replcd: ' + libname
                    else:
                        print '!found: ' + libname
            if not replaced:
                print 'danger? ' + libname
        
def walkDirectory( rootDir ):
    print('walking from root directory '+rootDir)
    for root, dirs, files in os.walk(rootDir):
        for fname in files:
            if fname.endswith('.dylib'):
                examineFile( os.path.join(root, fname) )

try:
    import argparse
    parser = argparse.ArgumentParser(description='List or replace absolute paths to dylibs.')
    parser.add_argument('rootDir', metavar='filename', type=string, default='.',
                        help='individual file or directory')
    parser.add_argument('--replace', dest='do_replace', default=False,
                        help='run install_name_tool to replace paths; otherwise just list')
    args = parser.parse_args()
except ImportError:
    # argparse is new in Python 2.7
    rootDir = '.'
    do_replace = False
    if len(sys.argv)>1:
        rootDir = sys.argv[1]
    if len(sys.argv)>2 and sys.argv[2]=='replace':
        do_replace = True

if os.path.isdir( rootDir ):
    walkDirectory( rootDir )
else:
    # examine individual file
    examineFile( rootDir, do_replace )
