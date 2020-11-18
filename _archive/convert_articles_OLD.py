#! /usr/bin/env python
import pypandoc, bleach, sys, json
from bs4 import BeautifulSoup as Soup
from natsort import natsorted as nat
from pathlib import Path
from glob import glob

# pass in award / if award in subs.key JSON
AWARD_CODE = 'WARC-AWARDS'

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

def convert_docx(file, extract_media=True):
    '''
    Uses the pypandoc module to convert docx file to html content for parsing and extracts images.
    '''
    media = file.parent / file.stem
    try:
        media.mkdir(exist_ok=False)
    except FileExistsError as e:
        lgr.error(e)
    if extract_media:
        extra_args = [f'--extract-media={media}']
    else:
        extra_args = []
    contents = pypandoc.convert_file(str(file), 'html5', extra_args=extra_args) # find a way to extract to same folder rather than 'ID/media'
    return contents, media

def rename_docx_images(path, IMGS):
    '''
    Rename extracted images.
    Returns old img path and new img filename in a dict for subtitution in html.
    '''
    print('\n# renaming images...\n')
    try:
        files = {p.resolve() for p in Path(path).glob(r"**/*") if p.suffix.casefold() in [".jpeg", ".jpg", ".png", ".gif"]}
        for f in nat(files):
            ID = f.parent.parent.name # to get /<ID> rather than /media
            name = f.stem
            ext = f.suffix
            nums = [i for i in list(name) if i.isdigit()]
            num = ''.join(nums)
            n = "f" + num.zfill(2) 
            fn = f"{ID}{n}{ext}"
            fp = path / fn
            f.rename(fp)
            IMGS.update({f.name: f"/fulltext/{AWARD_CODE}/images/{fn}"})
            print(f'"{f.name}" --> {fn}')

        print(f"\n# renamed: {len(files)} images\n")
        return IMGS
    except Exception as e:
        raise e
    # else:
    #     print('no images to rename')

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

def amend_html(content, IMGS):
    '''
    Parses cleaned html content from docx, running replacements to correct headings.
    Heading substitutes are stored in json folder under '/json/subs.json'.
    Also contains the award code variable for inserting in <img src""/>.
    '''
    def wrap_img(ig):
        '''Wraps img in p tags.'''
        ig.wrap(tree.new_tag('p'))
        print('wrapped', ig)
        
    tree = Soup(content, "html.parser")
    # find all images, if images exist, replace the source attribute to renamed image
    images = tree.find_all('img')
    if images:
        for ig in images:
            src = ig['src']
            for k, v in IMGS.items(): # self.IMGS when class
                if k in src:
                    ig['src'] = src.replace(src, v)
                    print(f'<img src="{k}"> --> <img src="{v}">')
        if ig.parent.name == 'p':
            prt = ig.parent
            prt.insert_before('\n')
            prt.insert_after(ig) # insert all images outside of p tag to wrap them properly in p tags.
            wrap_img(ig)
             # strip whitespace and remove p tag if empty
            if len(prt.get_text(strip=True)) == 0: 
                print('cut', prt)
                prt.unwrap()
            ig.insert_before('\n')
        else:
            wrap_img(ig)
    else:
        print('no images...')

    # make all headers <p><strong>
    headers = tree.find_all(['h1','h2', 'h3','h4','h5'])
    if not headers:
        print('no headers to replace...')
    else:
        for hdr in headers:
            if hdr:
                hdr.string.wrap(tree.new_tag('strong'))
                hdr.name = 'p'
                print('header -->', hdr)
    # match all p tags with bold and check punctuation endings to filter bold sentences from subheadings in h5
    try:
        print('changing subheaders')
        paras = tree.find_all('p')
        for p in paras:
            if p.find('strong'):
                if p.text.endswith((".",",",":",";")):
                    pass
                else:
                    p.strong.unwrap()
                    p.name = 'h5'
                    print('<p><strong> -->', p)
        for li in tree.find_all('li'):
            if li.find('p'):
                li.p.unwrap()
                print('<li><p> -->', li)
    except AttributeError as e:
        print(e)

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
    # doc = Path(sys.argv[1])
    doc = Path('test/131485.docx')
    IMGS = {} # have this as global variable in class __init__
    if doc.suffix == '.docx':
        # extract_docx_images(doc)
        contents, media = convert_docx(doc)
        IMGS = rename_docx_images(media, IMGS)
    elif doc.suffix == '.html':
        with open(doc, encoding='utf-8') as f:
            contents = f.read()
    cleaned = clean_html(contents, TAGS)
    htmlcontent = amend_html(cleaned, IMGS)#.prettify()
    outfile = Path(f"{doc.parent}/{doc.stem}/{doc.stem}.htm")
    write_html(outfile, str(htmlcontent))

if __name__ == '__main__':
    main()
