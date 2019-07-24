import argparse
import json
import logging
import os
import subprocess
import time
from PIL import Image


# parse arguments
parser = argparse.ArgumentParser(description="Photo Organizer")
parser.add_argument('directory', type=str,
                    help='Directory to look for photos to save.')
parser.add_argument('--recursive', action='store_true',
                    help='Recursively search in directories')
parser.add_argument('--make-changes', action='store_true',
                    help='Make changes. Otherwise, just print data')
args = parser.parse_args()

# setup logging
logging.basicConfig(filename='organize.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# timing data
time_data = {
    'PIL_image_check': 0,
    'exiftool_check': 0
}


def get_create_year_month(filename):
    '''Return str of the year month YYYYMM of the create time of the file'''
    # Try to get create date using the PIL library. This works for images only,
    # but it's pretty fast.
    year_month = None
    try:
        start = time.time()
        im = Image.open(filename)
        exif_data = im.getexif()
        date_time_str = exif_data[36867]
        year_month = date_time_str[0:4] + date_time_str[5:7]
    except Exception:
        logger.info(f'Failed to get exif data from image {filename}')
    finally:
        end = time.time()
        time_data['PIL_image_check'] += (end - start)
    if year_month is not None:
        return year_month

    # Try to get create date using an external tool called exiftool. This works
    # with more file types (including movies, but it's slow).
    try:
        start = time.time()
        process_data = subprocess.run(["exiftool", filename, "-json",
                                       "-dateFormat", "%Y%m"], capture_output=True)
        if process_data.returncode == 0:
            output = json.loads(process_data.stdout)
            year_month = output[0]['CreateDate']
    except Exception as e:
        logger.info(f'Failed to get exif data from file {filename}. {e}')
    finally:
        end = time.time()
        time_data['exiftool_check'] += (end - start)

    # return year_month str (if found). Otherwise, this will be None.
    return year_month


# Get files to check
filenames = set()
base_dir = args.directory
for f in os.listdir(base_dir):
    fullpath = os.path.join(base_dir, f)
    if os.path.isfile(fullpath):
        filenames.add(fullpath)
logger.info(f'Found {len(filenames)} to organize.')

# make dictionary for directory to put files
file_to_dir = {}
num_failed = 0
num_to_move = 0
for a_file in filenames:
    create_date = get_create_year_month(a_file)
    if create_date is not None:
        file_to_dir[a_file] = str(create_date)
        num_to_move += 1
        logger.info(f"Will move {a_file} into {create_date}/")
    else:
        num_failed += 1
        logger.info(f"Could not find create date for {a_file}")

logger.info(
    f"Will move {num_to_move} files. Failed to find date of {num_failed} files.")

logger.info(
    f"Timing data: {time_data}")

# Move files to directories
for f, d in file_to_dir.items():
    basename = os.path.basename(f)
    target_dir = os.path.join(base_dir, d)
    target_file = os.path.join(target_dir, basename)
    if os.path.exists(target_file):
        logger.error(f'File already exists: {target_file}')
        continue

    logger.info(f'will move {f} ({basename}) to {target_file}')
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    os.rename(f, target_file)
