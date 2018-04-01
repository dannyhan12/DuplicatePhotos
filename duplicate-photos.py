import argparse
import hashlib
import logging
import os

# setup hash function to convert bytes into a sequence
def getHash(filename):
    ''' Return str sequence that represents the bytes in a file '''
    hasher = hashlib.md5()
    BLOCKSIZE = 65536
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

# parse arguments
parser = argparse.ArgumentParser(description="Duplicate Photo Finder")
parser.add_argument('directories', nargs='+', type=str,
                    help='Directories to search.')
parser.add_argument('--recursive', action='store_true',
                    help='Recursively search in directories')
args = parser.parse_args()

# setup logging
FORMAT = '%(asctime)s %(filename)s:%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


# Get files to check
filenames = set()
for d in args.directories:
    for f in os.listdir(d):
        fullpath = os.path.join(d,f)
        if os.path.isfile(fullpath):
            filenames.add(fullpath)

# make dictionary for md5 to a list with same file to file name
hashToFilenames = {}
for aFile in filenames:
    hashValue = getHash(aFile)
    logger.debug(f"{aFile} -- {hashValue}")
    if hashValue in hashToFilenames:
        hashToFilenames[hashValue].append(aFile)
    else:
        hashToFilenames[hashValue] = [aFile]


# output duplicates
for hashValue,duplicates in hashToFilenames.items():
    if len(duplicates) > 1:
        logger.warn(f"duplicate found for {duplicates}")
