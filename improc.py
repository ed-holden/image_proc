#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import os
import pyexiv2
import re
import sys
import unicodedata

from optparse import OptionParser, OptionGroup
from time import strftime, gmtime

ARTIST_NAME = 'Ed Holden'

# Set this dictionary to map frequently-used locations
FREQUENT_LOCATIONS = {
    'a': 'Arlington, MA', 'b': 'Boston, MA', 'c': 'Cambridge, MA',
    'n': 'Newington, CT', 'r': 'Rochester,NY', 's': 'Somerville, MA'}

# Default GMT conversion to local time
GMT_OFFSET = '-5'


class Error(Exception):
  """Base class for exceptions."""


class BadRequestError(Error):
  """Exception raised when user request is invalid."""


def timeShift(image_datetime, timeshift):
  """Shift time forward/backward by X hours, as supplied by the timeshift option.

  Args:
    image_datetime: datetime, The timestamp taken from the file in some way.
    timeshift: str, A number of hours by which to shift the timestamp, with a +
        or - symbol and an integer.
  Returns:
    A revised datetime object.
  """
  try:
    if timeshift[0] == '+':
      new_image_datetime = image_datetime + datetime.timedelta(hours=int( timeshift[1] ) )
    elif timeshift[0] == "-":
      new_image_datetime = image_datetime - datetime.timedelta(hours=int( timeshift[1] ) )
    else:
      raise TypeError

  except TypeError:
    print 'Error: Malformed timeshift supplied (should be "+X" or "-X" where X is an integer)'
    sys.exit()

  return new_image_datetime


def convertToAscii(nameString):
  """Make a string ASCII-safe, swapping some characters for ASCII equivalents."""
  translations = {
      8226: '*',   # translate '•'
      171: '"',   # translate '«'
      187: '"',   # translate '»'
      196: 'A',   # translate 'Ä'
      197: 'A',   # translate 'Å'
      199: 'C',   # translate 'Ç'
      201: 'E',   # translate 'É'
      209: 'N',   # translate 'Ñ'
      214: 'Oe',  # translate 'Ö'
      220: 'U',   # translate 'Ü'
      225: 'a',   # translate 'á'
      224: 'a',   # translate 'à'
      226: 'a',   # translate 'â'
      228: 'ae',  # translate 'ä'
      227: 'a',   # translate 'ã'
      229: 'a',   # translate 'å'
      231: 'c',   # translate 'ç'
      233: 'e',   # translate 'é'
      232: 'e',   # translate 'è'
      234: 'e',   # translate 'ê'
      235: 'e',   # translate 'ë'
      237: 'i',   # translate 'í'
      236: 'i',   # translate 'ì'
      238: 'i',   # translate 'î'
      239: 'i',   # translate 'ï'
      241: 'n',   # translate 'ñ'
      243: 'o',   # translate 'ó'
      242: 'o',   # translate 'ò'
      244: 'o',   # translate 'ô'
      246: 'o',   # translate 'ö'
      245: 'o',   # translate 'õ'
      250: 'u',   # translate 'ú'
      249: 'u',   # translate 'ù'
      251: 'u',   # translate 'û'
      252: 'u',   # translate 'ü'
      8224: '*',  # translate '†'
      176: '*',   # translate '°'
      162: 'c',   # translate '¢'
      163: '#',   # translate '£'
      167: 'S',   # translate '§'
      182: 'P',   # translate '¶'
      174: '(R)', # translate '®'
      169: '(c)', # translate '©'
      8482: '(TM)', # translate '™'
      180: "'",   # translate '´'
      168: "'",   # translate '¨'
      8800: '<>', # translate '≠'
      198: 'AE',  # translate 'Æ'
      216: 'O',   # translate 'Ø'
      8734: '()()', # translate '∞'
      177: '+/-', # translate '±'
      8804: '<=', # translate '≤'
      8805: '>=', # translate '≥'
      165: 'Yen', # translate '¥'
      181: 'u',   # translate 'µ'
      8706: 'd',  # translate '∂'
      8721: 'Sum', # translate '∑'
      8719: 'PI', # translate '∏'
      960: 'pi',  # translate 'π'
      8747: 'Int', # translate '∫'
      170: 'a',   # translate 'ª'
      186: 'o',   # translate 'º'
      937: 'Ohm', # translate 'Ω'
      230: 'ae',  # translate 'æ'
      248: 'o',   # translate 'ø'
      191: '?',   # translate '¿'
      161: '!',   # translate '¡'
      172: '-',   # translate '¬'
      8730: '/',  # translate '√'
      402: 'f',   # translate 'ƒ'
      8776: '=',  # translate '≈'
      8230: '...', # translate '…'
      192: 'A',   # translate 'À'
      195: 'A',   # translate 'Ã'
      213: 'O',   # translate 'Õ'
      338: 'OE',  # translate 'Œ'
      339: 'oe',  # translate 'œ'
      8211: '-',  # translate '–'
      8212: '--', # translate '—'
      8220: '"',  # translate '“'
      8221: '"',  # translate '”'
      8216: "'",  # translate '‘'
      8217: "'",  # translate '’'
      247: '/',   # translate '÷'
      9674: 'o',  # translate '◊'
      255: 'ye',  # translate 'ÿ'
      376: 'Ye',  # translate 'Ÿ'
      8364: 'O',  # translate '€'
      8249: '<',  # translate '‹'
      8250: '>',  # translate '›'
      8225: '*',  # translate '‡'
      183: '.',   # translate '·'
      8218: ',',  # translate '‚'
      8222: ',',  # translate '„'
      8240: '0/00', # translate '‰'
      194: 'A',   # translate 'Â'
      202: 'E',   # translate 'Ê'
      193: 'A',   # translate 'Á'
      203: 'Ee',  # translate 'Ë'
      200: 'E',   # translate 'È'
      205: 'I',   # translate 'Í'
      206: 'I',   # translate 'Î'
      207: 'I',   # translate 'Ï'
      204: 'I',   # translate 'Ì'
      211: 'O',   # translate 'Ó'
      212: 'O',   # translate 'Ô'
      210: 'O',   # translate 'Ò'
      218: 'U',   # translate 'Ú'
      219: 'U',   # translate 'Û'
      217: 'U',   # translate 'Ù'
      710: '^',   # translate 'ˆ'
      732: '~',   # translate '˜'
      175: "'",   # translate '¯'
      184: ','    # translate '¸'
  }

  unicode_string=nameString.decode('utf-8')
  revised_name = ''

  for character in unicode_string:
    ord_character = ord(character)
    if ord_character in translations:
      revised_name += translations[ord_character]
    else:
      revised_name += character
  return revised_name


def getFileDateTime(image_filename, image_metadata, verbose=False):
  """Obtain the datestamp for the file for naming purposes, by any means.

  First we try to get this from EXIF data. But some cameras, some functions of
  cameras, and some photos from online services lack EXIF metadata on JPEGs. So
  we need to check whether there is a datestring in the filename itself, which
  is a nice freebie, and failing that we can use the filesystem modification
  time. These are in UTC in seconds from epoch, so we need to use the
  GMT_OFFSET value on it.

  Args:
    image_filename: A string contianing an image file's name.
    image_metadata: A pyexiv2 ImageMetadata object extracted from said file.
    verbose: bool, express verbosity

  Returns:
    A datetime object.
  """
  try:
    image_file_datetime = image_metadata['Exif.Photo.DateTimeOriginal'].value
  except KeyError:
    matched_datestring = re.match(
        '.*(2[0-9]{3})([0-9]{2})([0-9]{2})[-_]*'
        '([0-9]{2})([0-9]{2})([0-9]{2}).*', image_filename)
    if matched_datestring:
      image_file_datetime = datetime.datetime(
          int(matched_datestring.group(1)), int(matched_datestring.group(2)),
          int(matched_datestring.group(3)), int(matched_datestring.group(4)),
          int(matched_datestring.group(5)), int(matched_datestring.group(6)))
    else:
      if verbose:
        print 'Error: Metadata read failed for', image_filename + '; trying file modification date ...'
      file_stat = os.stat(image_filename)

      # GMT conversion in seconds
      GMT_OFFSETSeconds = int(GMT_OFFSET[1]) * 3600
      if GMT_OFFSET[0] == "-":
        GMT_OFFSETSeconds = 0 - GMT_OFFSETSeconds

      # Pass st_mtime (most recent content modification in seconds from epoch)
      # to strftime to render it sensible
      fileModDatetime = strftime("%Y%m%d%H%M%S", gmtime(file_stat[8] + GMT_OFFSETSeconds))

      image_file_datetime = datetime.datetime(
          int(fileModDatetime[0:4]), int(fileModDatetime[4:6]),
          int(fileModDatetime[6:8]), int(fileModDatetime[8:10]),
          int(fileModDatetime[10:12]), int(fileModDatetime[12:14]))

  return image_file_datetime


def PrepareJpegFiles(file_list, timeshift, verbose=False):
  """Prepare images, renaming them to datestring number names with no extension.
  To do this all specified files are analyzed for metadata date and time and
  renamed like:

    20120420-12345600

  The first eight characters are the datestring, and the 123456 is the hour,
  minute, second, and a trailing "00" to allow multiple pictures during the same
  second. Additionally, the function analyzes the orientation metadata and
  resets it to 1, and issue the jpegtran command to rotate the photo accordingly.
  When we re-save the metadata, we'll put the original filename in the user
  comment field.

  Args:
    file_list: list, of files
    timeshift: str, the amount of time by which to shift the timestamp, with a +
        or - symbol and an integer.
    verbose: bool, express verbosity
  """
  image_file_info = {}
  images_per_second = {}

  def padDate(date_element):
    """
    A function for padding a single digit to a double, as in 3 -> 03
    """
    timestring = str(date_element)
    if len(timestring) == 1:
      return '0' + timestring
    else:
      return timestring

  for image_filename in file_list:

    # Skip files that do not end in .jpg, .jpeg or caps equivalent
    jpeg_extension_re = re.compile(r".*\.[Jj][Pp][Ee]{0,1}[Gg]$")
    if not jpeg_extension_re.match(image_filename):
      print '\tNotification: Skipping file', image_filename
      continue

    # Make sure file is writable
    os.chmod(image_filename, 0777)

    image_metadata = pyexiv2.ImageMetadata(image_filename)
    try:
      image_metadata.read()
    except IOError as e:
      print '\n\tError: Cannot read %s metadata (reasons below).\n\n%s' % (image_filename, e)

    image_file_datetime = getFileDateTime(image_filename, image_metadata)

    # Add or subtract hours in acccordance with timeshift option, if it was supplied
    if timeshift:
      image_file_datetime = timeShift(image_file_datetime, timeshift)

    image_file_timestring = (
        str(image_file_datetime.year) + padDate(image_file_datetime.month) +
        padDate(image_file_datetime.day) + "-" + padDate(image_file_datetime.hour) +
        padDate(image_file_datetime.minute) + padDate(image_file_datetime.second))

    # Create a dictionary of the special datestring, mapped to a list of the filename and the metadata
    image_file_info[image_filename] = image_metadata

    # Make a list of files for each second (e.g., 20130101-123401) in case of fast camera work
    if images_per_second.get(image_file_timestring):
      images_per_second[image_file_timestring].append(image_filename)
      images_per_second[image_file_timestring].sort()
    else:
      images_per_second[image_file_timestring] = [image_filename,]

  # A list of files in the order in which they were taken regardless of source
  image_file_datetimes = images_per_second.keys()
  image_file_datetimes.sort()

  image_count = 1

  # Process the files for each second in order of original filename
  for image_file_datetime in image_file_datetimes:

    imagesPerThisSecond = len(image_file_datetime)
    imagePerSecondCount = 0

    for image_filename in images_per_second[image_file_datetime]:

      if imagesPerThisSecond > 0:
        try:
          new_filename = image_file_datetime + padDate(imagePerSecondCount)
          imagePerSecondCount += 1
        except IndexError:
          print "No more than 26 images per second. That's how many letters we have"
          sys.exit()
      else:
        new_filename = image_filename

      image_metadata = image_file_info[image_filename]
      image_metadata.read()

      # Add the original filename to the description comment for posterity
      image_metadata['Exif.Photo.UserComment'] = pyexiv2.ExifTag(
          'Exif.Photo.UserComment', '(Original filename was ' + image_filename + ')')

      # Determine whether to rotate based on Orientation tag
      # 0 = normal, 1 = 180, 6 = 90 CW, 9 = 90 CCW, 8 = 270 CW, 2 = 270 CCW
      try:
        image_orientation = image_metadata['Exif.Image.Orientation'].value
        if (image_orientation > 1):
          required_rotation = True
        else:
          required_rotation = False
      except KeyError:
        required_rotation = False

      try:
        image_metadata.write()
      except ValueError:
        print "\n\tError: Cannot write metadata to file " + image_filename + " - image valid?"

      if required_rotation:
        rotation_notification = " and rotating based on orientation tag"
        os.system('exiftran -aig ' + image_filename + ' > /dev/null 2>&1')
      else:
        rotation_notification = ""

      if verbose:
        print (
            'Image %d of %d: Renaming %s to %s%s' %
            (image_count, len(file_list), image_filename, new_filename, rotation_notification))

      os.rename(image_filename, new_filename)
      image_count += 1


def WriteFile(image_filename, new_title, verbose=False):
  """
  Write custom metadata for a given image file and rename it.

  Args
    image_filename - string, the present filename of the image
    new_title - string, the new title from which we will make metadata and a
        new filename
    verbose - bool, express verbosity
  """
  new_filename = new_title + '.jpg'
  safe_title = convertToAscii(new_title)

  image_metadata = pyexiv2.ImageMetadata(image_filename)
  try:
    image_metadata.read()
  except IOError as e:
    print '\n\tError: Cannot read %s metadata (reasons below).\n\n%s' % (image_filename, e)

  # We can't use <dict>.get() on an Image object so we must handle KeyErrors
  try:
    old_usercomment = image_metadata['Exif.Photo.UserComment'].value
  except KeyError:
    old_usercomment = ''

  image_metadata['Exif.Image.ImageDescription'] = pyexiv2.ExifTag('Exif.Image.ImageDescription', safe_title)
  image_metadata['Exif.Image.DocumentName'] = pyexiv2.ExifTag('Exif.Image.DocumentName', safe_title)
  image_metadata['Exif.Photo.UserComment'] = pyexiv2.ExifTag('Exif.Photo.UserComment', new_title + "\n" + old_usercomment)
  image_metadata['Exif.Image.Artist'] = pyexiv2.ExifTag('Exif.Image.Artist', ARTIST_NAME)
  image_metadata['Exif.Image.Copyright'] = pyexiv2.ExifTag('Exif.Image.Copyright', "Copyright " + new_title[:4] + " " + ARTIST_NAME)
  try:
    image_metadata.write()
  except IOError:
    print '\n\tError: EXIF data could not be written for "' + new_filename + '" (formerly "' + image_filename + '")\n'
    print image_metadata

  if verbose: print 'Naming "' + new_filename + '" (formerly "' + image_filename + '")'
  try:
    os.rename(image_filename, new_filename)
  except:
    print 'Cannot rename ' + image_filename


def FinalizeJpegFiles(file_list, begin, until, verbose, sanity_check):
  """Finalize images, naming them based upon notation and including metadata.

  Filenames that went through the prepare proces originally looked like this:

    20120420-12345600

   The user then renamed them something like:

    20120420-12345600L"Arlington, MA"S"Spy Pond Park"Kids on the swings

   where L"..." and the S"..." are optional location and sublocation strings. Here we rename the file:

    20120420-12345600 Arlington, MA - Spy Pond Park - Kids on the swings.jpg

  Args
    file_list - list, of filenames
    begin - string, the datetime before which we should not process images
    until - string, the datetime beyond which we should stop processing images
    verbose - bool, express verbosity
    sanity_check - don't do the operation, just present what would happen
  """

  for image_filename in file_list:

    # Skip some files with invalid filenames, including filename extensions
    invalidFileRe = re.compile(r"^\..*|^[Ii][Mm].*|^[Vv][Ii].*|.*\.[A-Za-z]{3}")
    if invalidFileRe.match(image_filename):
      print "\tNotification: Skipping file", image_filename
      continue

    # Don't process before we reach a file whose date string comes after our 'begin'
    if begin:
      try:
        if int(image_filename[:8]) < int(begin):
          continue
      except ValueError:
        continue
      except AttributeError:
        pass

    # Stop processing when we reach a file whose date string comes after our 'until'
    if until:
      try:
        if int(image_filename[:8]) > int(until):
          break
      except AttributeError:
        pass

    # Look to see if there is a date at the beginning of the filename. Fail if not.
    dateExtractRe = re.compile(r"^([0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])(.*)$")
    try:
      dateString, userString = dateExtractRe.search(image_filename).group(1,2)
    except AttributeError:
      print "\n\tError: Failed to process", image_filename

    # Look to see if there is a location. If there is, we'll keep reusing it on each new file.
    # If there is not, and we have no previous location from a previous pass, we fail.
    locationExtractRe = re.compile(r"^L\"([^\"]+)\"")
    try:
      extractedLocation = locationExtractRe.search(userString).group(1)
      new_location = True

      # If we have a one-character location, we should check the frequent dictionary,
      # e.g., "a" would translate to frequentlocations[a]
      if len(extractedLocation) == 1:
        try:
          location = FREQUENT_LOCATIONS[extractedLocation] + " - "
        except KeyError:
          raise Exception, image_filename
      else:
        location = extractedLocation + " - "

    except AttributeError:
      try:
        location
        new_location = False
      except NameError:
        print "\n\tError: No location specified or inherited for file \"" + image_filename + "\""
        sys.exit()

    # Look to see if there is a sublocation (optional!)
    sublocationExtractRe = re.compile(r".*S\"([^\"]+)\"")
    try:
      sublocation = sublocationExtractRe.search(userString).group(1)
    except AttributeError:
      try:
        # If object exists from previous loop, we make it empty ("none") if there is a new location, assuming a new
        # location demands a new sublocation, or no sublocation.
        sublocation
        if new_location == True:
          sublocation = "none"
      except NameError:
        sublocation = "none"

    # Grab the rest
    descriptionExtractRe = re.compile(r"\s*([^\"]+)\s*$")
    try:
      description = descriptionExtractRe.search(userString).group(1)
    except AttributeError:
      try:
        description
      except NameError:
        description = "none"

    # Allow us to say "none" for sublocation and have none, stripping out the end dash from the location
    new_title = dateString + " " + location
    if sublocation != "none":
      new_title = new_title + sublocation + " - "

    # Allow us to say "none" for description and have none, stripping out the end dash from the location or sublocation
    if description == "none":
      new_title = new_title[:-3]
    else:
      new_title = new_title + description

    if sanity_check:
      if verbose: print 'Sanity check: propose creating "' + new_title + '" (formerly ' + image_filename + ')'
    else:
      WriteFile(image_filename, new_title, verbose)


def Regex(file_list, simple_regex, verbose=False):
  """
  Swap text in already-processed filenames and file metadata.

  Args
    file_list - a list of local filenames in the current working directory
    simple_regex - a string of format "original text/new text"

  """
  regex_re = re.match(r"(.+)/(.+)", simple_regex) 
  old_string, new_string = regex_re.group(1), regex_re.group(2)

  for image_filename in file_list:
    image_title_re = re.match(r"(.+)\.jpg$", image_filename)
    if image_title_re:
      image_title = image_title_re.group(1)

      if old_string != new_string:
        new_title = re.sub(old_string, new_string, image_title)
        WriteFile(image_filename, new_title, verbose)


if __name__ == '__main__':

  parser = OptionParser()
  parser.add_option(
      '-p', '--prepare', action='store_true', dest='prepare', default=False,
      help=(
          'Prepare by setting orientation to 0 (no rotate) in JPEG Exif data, '
          'and by rotating some images and renaming all of them with simple '
          'numbers'))
  parser.add_option(
      '-f', '--finalize', action='store_true', dest='finalize', default=False,
      help=(
          'Finalize images by renaming them with a datestamp, sequence number '
          'and location (if any); also set descriptive JPEG Exif data based '
          'upon filename'))
  parser.add_option(
      '-d', '--directory', action='store', type='string', dest='directory',
      default='.', help=(
          'Specify directory containing images in which to run app'))
  parser.add_option(
      '-v', '--verbose', action='store_true', dest='verbose', default=False,
      help='Print verbose status messages')

  prepare_group = OptionGroup(
      parser, 'Prepare Options',
      'Options that can be used with with -p (prepare mode).')
  prepare_group.add_option(
      '-t', '--timeshift', action='store', type='string', dest='timeshift',
      help=(
          'Shift time by X hours, where X is an integer, by supplying "+X" or '
          '"-X" (quotes required)'))
  parser.add_option_group(prepare_group)

  finalize_group = OptionGroup(
      parser, 'Finalize Options',
      'Options that can be used with with -f (finalize mode).')
  finalize_group.add_option(
      '-b', '--begin', action='store', type='string', dest='begin', default='',
      help=(
          'Specify timstamp in ISO YYYYMMDD format before which the app will '
          'not process images during finalization.'))
  finalize_group.add_option(
      '-s', '--sanity_check', action='store_true', dest='sanity_check',
      default=False, help=(
          'Output filename changes to STDOUT, but do not make the name '
          'changes, nor the metadata changes; available in finalize only.'))
  finalize_group.add_option(
      '-u', '--until', action='store', type='string', dest='until', default='',
      help=(
          'Specify timstamp in ISO YYYYMMDD format beyond which the app will '
          'not process images during finalization.'))
  parser.add_option_group(finalize_group)

  completed_group = OptionGroup(
      parser, 'Post-finalize Options',
      'Options that can be used on completed images.')
  completed_group.add_option(
      '-c', '--change_date', action='store', type='string', dest='change_date',
      help=(
          'Change the datestamp, which will not alter the location or '
          'image sequence number'))
  completed_group.add_option(
      '-m', '--move_location', action='store', type='string',
      dest='move_location', help=(
          'Move location (i.e., change the location name on images), which '
          'will not alter the date or image sequence number'))
  completed_group.add_option(
      '-r', '--regex', action='store', type='string', dest='regex', default='',
      help=(
          'Supply a simple regular expression substitution in the format '
          '"original-string/replacement-string" to apply to existing, '
          'finished images'))
  parser.add_option_group(completed_group)

  options, remainder = parser.parse_args()

  # Only bother with the --until or --begin option if we are finalizing
  if options.finalize:
    dateExtractRe = re.compile(r'^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$')
    if options.until:
      if not dateExtractRe.match(options.until):
        raise BadRequestError('Error: Invalid date string for "until" option')
    if options.begin:
      if not dateExtractRe.match(options.begin):
        raise BadRequestError('Error: Invalid date string for "begin" option')

  # Get a list of files in the desired directory
  file_list = os.listdir(options.directory)
  file_list.sort()

  originalCwd = os.getcwd()
  os.chdir(options.directory)

  if options.prepare:
    PrepareJpegFiles(file_list, options.timeshift, options.verbose)

  if options.finalize:
    FinalizeJpegFiles(file_list, options.begin, options.until, options.verbose, options.sanity_check)

  if options.regex:
    Regex(file_list, options.regex, options.verbose)

  # Return to old cwd
  os.chdir(originalCwd)
