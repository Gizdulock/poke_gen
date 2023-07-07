def decode_html_content(self, soup):
    # Here we'll use BeautifulSoup to parse the HTML and decode the dynamic content
    decoded_content = ""
    for tag in soup.find_all():
        if tag.name == "a":
            decoded_content += f"Link: {tag.get('href')}\n"
        elif tag.name == "img":
            decoded_content += f"Image: {tag.get('src')}\n"
        elif tag.name == "p":
            decoded_content += f"Text: {tag.text}\n"
        else:
            decoded_content += f"{tag.name}: {tag.text}\n"
    return decoded_content