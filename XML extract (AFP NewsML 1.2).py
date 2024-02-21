# %%
import os
import pandas as pd
from collections import deque
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# %%
def extract_author_or_provider(file_path):
    '''Function to XML extract author information,
      or provider information as a fallback'''
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # First, try to find author information
        for byline in root.iter('ByLine'):
            author_name = byline.text
            return author_name  # Return author name if found

        # If author is not found, try to find provider information
        for provider in root.iter('Provider'):
            party = provider.find('Party')
            if party is not None and 'FormalName' in party.attrib:
                provider_name = party.attrib['FormalName']
                return provider_name  # Return provider name if found

        # Return None if neither author nor provider is found
        return None

    except ET.ParseError:
        return "XML Parse Error"

# %%
def parse_headlines(root):
    """
    Refactored function to parse the XML root to extract the headline or an alternative text
    when the headline is not explicitly found.

    Args:
    root (Element): The root element of the parsed XML document.

    Returns:
    str: The extracted headline or alternative text, or an appropriate message if not found.
    """
    try:
        # Looking for the HeadLine tag within the NewsLines section
        headline = root.find('.//NewsLines/HeadLine')
        if headline is not None and headline.text is not None:
            return headline.text.strip()
        else:
            # If the headline is not found or empty, look for the first paragraph in body.content
            first_paragraph = root.find('.//body.content/p')
            if first_paragraph is not None and first_paragraph.text is not None:
                return first_paragraph.text.strip()
            else:
                return "Headline or alternative text not found in the file."
    except Exception as e:
        return f"Error processing the XML: {e}"

# %%
def extract_content(root):
    """
    Extract news text from <DataContent> within <ContentItem> tags.

    Args:
    root (ET.Element): The root of the ET tree.

    Returns:
    str: The extracted news text.
    """
    news_text = []

    # Find all <ContentItem> tags and then extract text from <DataContent> <p> tags
    for content_item in root.findall('.//ContentItem'):
        for data_content in content_item.findall('.//DataContent'):
            for p in data_content.findall('.//p'):
                if p.text:
                    news_text.append(p.text)

    return '\n'.join(news_text)

# %%
def parse_newsml_xml(file_path):
    """
    Parse a NewsML XML file and extract the required information.

    :param file_path: Path to the NewsML XML file.
    :return: Dictionary with extracted data.
    """
    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Initialize data dictionary
        news_data = {
            'Headline': None,
            'Topic': None,
            'Tags': None,
            'Authors': None,
            'Date': None,
            'Content': None,
            'Location': None
        }

        # Extracting Headline
        news_data['Headline'] = parse_headlines(root)

        # Extracting Topic (NameLabel)
        topic = root.find(".//Identification/NameLabel")
        if topic is not None:
            news_data['Topic'] = topic.text

        # Extracting Tags (OfInterestTo)
        tags = root.findall(".//DescriptiveMetadata/OfInterestTo")
        if tags:
            tags = ', '.join([tag.get('FormalName') for tag in tags if tag.get('FormalName')])
            news_data['Tags'] = tags.replace('--', ', ')
        else:
            news_data['Tags'] = None

        # Extracting Date (FirstCreated)
        date = root.find(".//NewsManagement/FirstCreated")
        if date is not None:
            date_text = date.text
            try:
                # First, try to parse without timezone assuming UTC ('Z' at the end)
                datetime_obj = datetime.strptime(date_text, "%Y%m%dT%H%M%SZ")
                datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)
            except ValueError:
                # Next, try to parse with timezone offset
                datetime_obj = datetime.strptime(date_text, "%Y%m%dT%H%M%S%z")
                # Convert to UTC
                datetime_obj = datetime_obj.astimezone(timezone.utc)

            # Format the datetime object to ISO 8601 format in UTC
            news_data['Date'] = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S%z")


        # Extracting Location
        location = root.find(".//Location")
        if location is not None:
            country = location.find(".//Property[@FormalName='Country']")
            city = location.find(".//Property[@FormalName='City']")
            location_text = ''
            if city is not None:
                location_text += city.get('Value')
            if country is not None:
                location_text += ', ' + country.get('Value') if location_text else country.get('Value')
            news_data['Location'] = location_text

        # TODO: Extract Authors and Content once their structure is understood
            
        # Extracting Authors
        news_data['Authors'] = extract_author_or_provider(file_path)

        # Extracting Content
        news_data['Content'] = extract_content(root)

        return news_data

    except ET.ParseError:
        return {'error': 'Failed to parse XML file'}


# %%
def process_xml_files_iteratively(folder_path):
    """
    Iteratively searches through the folder tree for XML files, applies dummy_function to each,
    and counts the number of files processed for each path.
    """
    xml_count = {}
    content_list = []
    queue = deque([folder_path])  # Initialize the queue with the root folder

    while queue:
        current_path = queue.popleft()  # Get the next directory to process
        current_count = 0

        # Attempt to list directories and files in the current_path
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_dir():
                        queue.append(entry.path)  # Add subdirectories to the queue
                    elif entry.is_file() and entry.name.endswith('.xml'):
                        content_list.append(parse_newsml_xml(entry.path))
                        current_count += 1
        except PermissionError:
            print(f"Permission denied: {current_path}")

        if current_count > 0:
            xml_count[current_path] = current_count

    for x in xml_count:
        print(f'Processed {xml_count[x]} files in {x}')

    df = pd.DataFrame(content_list)
    return df

content = process_xml_files_iteratively('afp')

# Save to csv
content.to_csv('parsed_xml.csv', index=False)