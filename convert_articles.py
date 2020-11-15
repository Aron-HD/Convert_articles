#! /usr/bin/env python
from bs4 import BeautifulSoup as Soup
# from pathlib import Path
# from glob import glob
import bleach, pypandoc, sys#, json



tags = [
    'img','h1','h2', 'h3','h4','h5','br',
    'b', 'strong', 'em', 'i', 'u', 'a', 'p',
    'ul', 'li', 'ol'
    ]
attrs = {
    'a': ['href'],
    'img': ['src','alt'],
    'ul': ['start', 'type'],
    'ol': ['start', 'type']
    }

AWARD_CODE = 'WARC-AWARDS-MEDIA'

# get these images written to JSON dict and pased in
imgs = {
    "media/image1.jpg": f"/content/{AWARD_CODE}/133341f01",
    "media/image2.jpg": f"/content/{AWARD_CODE}/133341f02",
    "media/image3.jpg": f"/content/{AWARD_CODE}/133341f03"
}
def convert_docx(file):
    contents = pypandoc.convert_file(file, 'html')
    return contents

def clean_html(content):
    cleaned = bleach.clean(content,
        attributes=attrs,
        tags=tags,
        strip=True
    )
    return cleaned

def amend_html(content):
    tree = Soup(content, "html.parser")

    # find all images, if images exist,
    # replace the source attribute to renamed image
    images = tree.find_all('img')
    if images:
        for i in images:
            if i:
                src = i['src']
                for k, v in imgs.items():
                    if k in src:
                        i["src"] = src.replace(k, v)
                        print(f'<img src="{k}"> --> <img src="{v}">')
    else:
        print('no images...')
    # replacements for titles.
    # for header in headers
    # if end with fullstop or punctuation make them <p><strong>
    # else if they
    headers = tree.find_all(['h1','h2', 'h3','h4','h5'])
    if headers:
        for hdr in headers:
            if hdr:
                hdr.string.wrap(tree.new_tag('strong'))
                hdr.name = 'p'
                print('header -->', hdr)
    else:
        print('no headers to replace...')
    # match all p tags with bold and check punctuation
    # endings to filter bold from subheadings in h5
    pstrongs = tree.find_all('p')
    for p in pstrongs:
        if p.find('strong'):
            if p.text.endswith((".",":","!","(",")",";")):
                pass
            else:
                p.name = 'h5'
                print('<p><strong> -->', p)

    for h5 in tree.find_all('h5'):
        if h5:
            h5.strong.unwrap()
            print('<h5><strong> -->', h5)

    # do final h3 changes to relevant award headers

    return tree

def write_html(file, contents):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(contents)
        print("wrote file:", file)

def main():
    '''
    if running from command line ./html_parse.py <file_you_want_to_convert>
    takes dictionary from image_replace.sh script of image conversion names, to sub them in document
    '''
    # document = sys.argv[1]
    # document = 'test/.docx'
    document = 'test/test.html'

    if '.docx' in document:
        contents = convert_docx(document)
    elif document.endswith('.html'):
        with open(document, encoding='utf-8') as f:
            contents = f.read()

    cleaned = bleachclean(contents)
    htmlcontent = htmlparse(cleaned)#.prettify()

    outfile = 'test/cleaned.html'
    write_final(outfile, str(htmlcontent))

if __name__ == '__main__':
    main()
