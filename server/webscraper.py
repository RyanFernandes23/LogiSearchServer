import requests
from bs4 import BeautifulSoup

def scrape_website(url, headers=None):
    """
    Scrape the website and return a BeautifulSoup object.
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page. Status code: {response.status_code}")
    
    return BeautifulSoup(response.text, 'html.parser')

def extract_elements(soup, element_type, class_name=None, id_name=None):
    """
    Extract specific elements (e.g., text, links, images) from the soup object.
    """
    if class_name:
        return soup.find_all(element_type, class_=class_name)
    elif id_name:
        return soup.find_all(element_type, id=id_name)
    else:
        return soup.find_all(element_type)

def extract_text(soup, class_name=None, id_name=None):
    """
    Extract text from paragraphs or other elements.
    """
    paragraphs = extract_elements(soup, 'p', class_name, id_name)
    return [p.get_text() for p in paragraphs]

def extract_links(soup, class_name=None, id_name=None):
    """
    Extract links from anchor tags.
    """
    links = extract_elements(soup, 'a', class_name, id_name)
    return [link.get('href') for link in links]

def extract_images(soup, class_name=None, id_name=None):
    """
    Extract image URLs from img tags.
    """
    images = extract_elements(soup, 'img', class_name, id_name)
    return [img.get('src') for img in images]

# Example usage
if __name__ == "__main__":
    url = "https://costafarms.com/blogs/get-growing/hardy-hibiscus-for-northern-climates"
    soup = scrape_website(url)

    # Extract text from paragraphs (generalized)
    text_content = extract_text(soup, class_name=None)  # Add class_name if needed
    print("Text Content:")
    for text in text_content:
        print(text)

# Extract links (generalized)
# links = extract_links(soup, class_name=None)  # Add class_name if needed
# print("\nLinks:")
# for link in links:
#     print(link)

# # Extract images (generalized)
# images = extract_images(soup, class_name=None)  # Add class_name if needed
# print("\nImages:")
# for img in images:
#     print(img)