#! /usr/bin/env python
from bs4 import BeautifulSoup as Soup
from pathlib import Path
# from glob import glob
import importlib.resources, pypandoc, bleach, sys, json

# pass in award / if award in subs.key JSON
AWARD_CODE = 'WARC-AWARDS-MEDIA'

# get these images written to JSON dict and pased in
imgs = {
    "media/image1.jpg": f"/content/{AWARD_CODE}/133341f01",
    "media/image2.jpg": f"/content/{AWARD_CODE}/133341f02",
    "media/image3.jpg": f"/content/{AWARD_CODE}/133341f03"
}

def load_json(file):
    '''
    Loads data from the specified json file.
    '''
    try:
        with open(file) as f:
            data = json.load(f)
            return data
    except Exception:
        raise

def convert_docx(file):
    '''
    Uses the pypandoc module to convert docx file to html content for parsing.
    '''
    ID = file.parent / file.stem
    print(ID)
    contents = pypandoc.convert_file(str(file), 'html5', extra_args=[f'--extract-media={ID}'])
    return contents

def rename_docx_images(file):
    '''
    Rename extracted images.
    Returns old img path and new img filename in a json for subtitution in html.
    '''
    pass
    return IMGS

def clean_html(content, TAGS):
    '''
    Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags.
    Tags and attributes are stored in json folder under '/json/tags.json'.
    '''
    cleaned = bleach.clean(content,
        attributes=TAGS['attrs'],
        tags=TAGS['tags'],
        strip=True
    )
    return cleaned

def amend_html(content):
    '''
    Parses cleaned html content from docx, running replacements to correct headings.
    Heading substitutes are stored in json folder under '/json/subs.json'.
    Also contains the award code variable for inserting in <img src""/>.
    '''
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
                        i['src'] = src.replace(k, v)
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
    # endings to filter bold sentences from subheadings in h5
    pstrongs = tree.find_all('p')
    for p in pstrongs:
        if p.find('strong'):
            if p.text.endswith((".",",",":",";")):
                pass
            else:
                p.name = 'h5'
                print('<p><strong> -->', p)

    for h5 in tree.find_all('h5'):
        if h5:
            h5.strong.unwrap()
            print('<h5><strong> -->', h5)
        else:
            pass

    # do final h3 changes to relevant award headers

    return tree

def write_html(file, contents):
    '''
    Outputs cleaned and amended html content to specified file name.
    Pass in file name and html contents.
    '''
    with open(file, 'w', encoding='utf-8') as f:
        f.write(contents)
        print("wrote file:", file)

def main():
    '''
# INSTRUCTIONS
- If running from command line: 
- `./convert_articles.py <file_you_want_to_convert>`

# FUNCTIONS
- load_json():
    Loads data from the specified json file.
- convert_docx(): 
    Uses the pypandoc module to convert docx file to html content for parsing.    
- rename_docx_images():
    Rename extracted images.
    Returns old img path and new img filename in a json for subtitution in html.
- clean_html():
    Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags.
    Tags and attributes are stored in json folder under '/json/tags.json'.
- amend_html():
    Parses cleaned html content from docx, running replacements to correct headings.
    Heading substitutes are stored in json folder under '/json/subs.json'.
    Also contains the award code variable for inserting in `<img src""/>`.
- write_html():
    Outputs cleaned and amended html content to specified file name.
    Pass in file name and html contents.
    '''
    SUBS = load_json('json_pkg/subs.json')
    TAGS = load_json('json_pkg/tags.json')

    # doc = sys.argv[1]
    doc = Path('test/131412.docx')
    # doc = 'test/test.html'

    if doc.suffix == '.docx':
        # extract_docx_images(doc)
        contents = convert_docx(doc)
    elif doc.suffix == '.html':
        with open(doc, encoding='utf-8') as f:
            contents = f.read()
    
    cleaned = clean_html(contents, TAGS)
    htmlcontent = amend_html(cleaned).prettify()

    # outfile = 'test/cleaned.html'
    outfile = Path(f"{doc.parent}/{doc.stem}/{doc.stem}.html")
    write_html(outfile, str(htmlcontent))

if __name__ == '__main__':
    main()