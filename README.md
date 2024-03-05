#  Extracting NewsML Data from XML files

NewsML specifies a standard format for news articles, which is used in many news and
media outlets. This project extracts headlines from XML files that follow this format
using [`xml.etree.ElementTree`](https://docs.python.org/3/library/xml.etree.elementtree.html).

Required values to parse are:
* Headline
* Topic
* Tags
* Authors
* Date
* Content
* Location

Some files are missing content (most noticeably `Tags`). Where there's no suitable alternative element, I’ve set them to `None`.

This project focussed solely on text extraction and ignored images.

Sample XML filers are found in `/afp`.
