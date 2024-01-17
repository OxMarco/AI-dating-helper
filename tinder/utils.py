import requests
import re

def contains_image_url(string: str) -> list:
    regex = r'https?:\/\/[^\s]+'

    urls = re.findall(regex, string)
    image_urls = []
    for url in urls:
        try:
            response = requests.head(url, timeout=5)

            if 'image' in response.headers.get('Content-Type', ''):
                image_urls.append(url)
        except requests.RequestException:
            # If there's an error (like a timeout), we just ignore this URL
            pass
    
    return image_urls


def strip_urls(string: str) -> str:
    regex = r'https?:\/\/[^\s]+'
    stripped_string = re.sub(regex, '', string)

    return stripped_string
