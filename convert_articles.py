#! /usr/bin/env python
import logging as log, sys, json, pypandoc, bleach 
from bs4 import BeautifulSoup as Soup
from natsort import natsorted as nat
from datetime import datetime
from pathlib import Path
from glob import glob

def log_setup(first_log, second_log):
    '''
    Makes log directory and sets logger file.
    Uses 'log' for main app, lgr1 for Article Class.
    '''
    fd = 'logs'                                                     # folder name
    ld = Path.cwd() / fd                                            # log directory
    ld.mkdir(exist_ok=True)                                         # ensure exists
    fn = Path(__file__).with_suffix('.log')                         # app filename
    lp = fd + '/%d_%m_%Y - (%H-%M-%S) - ' + f'{fn}'                 # path for log file
    nm = datetime.now().strftime(lp)                                # log name formatted
    log.basicConfig(level=log.DEBUG,                                # set up logging to file
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=nm,
                    filemode='w')
    cs = log.StreamHandler()                                        # define a Handler as console 
    cs.setLevel(log.INFO)                                           # write INFO messages or higher to the sys.stderr   
    fm = log.Formatter('%(name)-12s: %(levelname)-8s > %(message)s')# set a simpler format for console
    cs.setFormatter(fm)                                             # tell the handler to use this format
    log.getLogger('').addHandler(cs)                                # add the handler to the root logger
    log.info('setup logging')                                       # log to root
    lgr1 = log.getLogger(first_log)                                 # Define loggers for different areas of application
    lgr2 = log.getLogger(second_log)
    lgr1.debug(f'defined lgr1: {lgr1}')
    lgr2.debug(f'defined lgr2: {lgr2}')
    return lgr1, lgr2

lgr1, lgr2 = log_setup(first_log='ArticleClass',
                       second_log='Undefined')

class Article(object):
    '''
    # Article Class
    - Arguments:
        - IN_FILE: specify docx or html file.
        - TAGS: specify tags and attributes for bleach module in json file.
        - SUBS: specify substitutions for h3 headings in html.
    '''
    def __init__(self, IN_FILE, TAGS, SUBS, AWARD):
        # super(Article, self).__init__()
        self.IN_FILE = IN_FILE
        self.OUT_FILE = Path(f"{IN_FILE.parent}/{IN_FILE.stem}/{IN_FILE.stem}.htm")
        self.TAGS = TAGS
        self.SUBS = SUBS
        self.IMGS = {}
        self.MEDIA_PATH = IN_FILE.parent / IN_FILE.stem
        self.CONTENT = None
        self.AWARD_CODE = SUBS[AWARD]['code']
        try:
            self.MEDIA_PATH.mkdir(exist_ok=False)
            lgr1.info(f'made dir: {self.MEDIA_PATH}')
        except FileExistsError as e:
            lgr1.debug(e)
        
    def convert_docx(self, extract_media=True):
        '''
        Uses the pypandoc module to convert docx file to html content for parsing and extracts images.
        '''
        if extract_media:
            extra_args = [f'--extract-media={self.MEDIA_PATH}']
        else:
            extra_args = []
        self.CONTENT = pypandoc.convert_file(str(self.IN_FILE), 'html5', extra_args=extra_args) # find a way to extract to same folder rather than 'ID/media'

    def rename_docx_images(self):
        '''
        Rename extracted images.
        Returns old img path and new img filename in a dict for subtitution in html.
        '''
        path = self.MEDIA_PATH
        if not path:
            lgr1.info('no images to rename')
        else:
            try:
                lgr1.info('\n# renaming images...\n')
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
                    self.IMGS.update({f.name: f"/fulltext/{self.AWARD_CODE}/images/{fn}"})
                    lgr1.info(f'"{f.name}" --> {fn}')
                lgr1.info(f"\n# renamed: {len(files)} images\n")
            except Exception as e:
                lgr1.error('error while renaming files:', e)

    def clean_html(self):
        '''
        Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags.
        Tags and attributes are stored in json folder under '/json/tags.json'.
        '''
        self.CONTENT = bleach.clean(
            self.CONTENT,
            attributes=self.TAGS['attrs'],
            tags=self.TAGS['tags'],
            strip=True
        )
        # return cleaned

    def amend_html(self):
        '''
        Parses cleaned html content from docx, running replacements to correct headings.
        Heading substitutes are stored in json folder under '/json/subs.json'.
        Also contains the award code variable for inserting in <img src""/>.
        '''
        def wrap_img(ig):
            '''Wraps img in p tags.'''
            ig.wrap(tree.new_tag('p'))
            lgr1.info(f'wrapped: {ig}')
            
        tree = Soup(self.CONTENT, "html.parser")
        # find all images, if images exist, replace the source attribute to renamed image
        images = tree.find_all('img')
        if images:
            for ig in images:
                src = ig['src']
                for k, v in self.IMGS.items(): # self.IMGS when class
                    if k in src:
                        ig['src'] = src.replace(src, v)
                        lgr1.info(f'<img src="{k}"> --> <img src="{v}">')
            if ig.parent.name == 'p':
                prt = ig.parent
                prt.insert_before('\n')
                prt.insert_after(ig) # insert all images outside of p tag to wrap them properly in p tags.
                wrap_img(ig)
                 # strip whitespace and remove p tag if empty
                if len(prt.get_text(strip=True)) == 0: 
                    lgr1.info(f'cut {prt}')
                    prt.unwrap()
                ig.insert_before('\n')
            else:
                wrap_img(ig)
        else:
            lgr1.info('no images...')

        # make all headers <p><strong>
        headers = tree.find_all(['h1','h2', 'h3','h4','h5'])
        if not headers:
            lgr1.info('no headers to replace...')
        else:
            for hdr in headers:
                if hdr:
                    hdr.string.wrap(tree.new_tag('strong'))
                    hdr.name = 'p'
                    lgr1.info(f'header --> {hdr}')
        # match all p tags with bold and check punctuation endings to filter bold sentences from subheadings in h5
        try:
            lgr1.info('changing subheaders')
            paras = tree.find_all('p')
            for p in paras:
                if p.find('strong'):
                    if p.text.endswith((".",",",":",";")):
                        pass
                    else:
                        p.strong.unwrap()
                        p.name = 'h5'
                        lgr1.info(f'<p><strong> --> {p}')
            for li in tree.find_all('li'):
                if li.find('p'):
                    li.p.unwrap()
                    # lgr1.info(f'<li><p> --> {li}') # unicode error printing these in logs
                    print(f'<li><p> --> {li}')
        except AttributeError as e:
            lgr1.info(e)

        # do final h3 changes to relevant award headers
        self.CONTENT = tree
        # return tree

    def write_html(self):
        '''
        Outputs cleaned and amended html content to specified file name.
        Pass in file name and html contents.
        '''
        f = self.OUT_FILE
        with open(f, 'w', encoding='utf-8') as f:
            f.write(str(self.CONTENT))
            lgr1.info(f'wrote file: {f}')

def load_infile(infile):
    '''
    Runs validation on file input by sys.argv[1].
    '''
    log.debug(f'infile argument: {infile}')
    return infile

def load_award(award):
    '''
    Runs validation on award input by sys.argv[2] to return correct award code from SUBS json.
    '''
    log.debug(f'award argument: {award}')
    return award

def load_json(file):
    '''
    Loads data from the specified json file.
    '''
    log.debug(f'loaded JSON: {file}')
    try:
        with open(file) as f:
            data = json.load(f)
            return data
    except Exception as e:
        log.error('error loading json:', e)

def main():
    '''
# INSTRUCTIONS

- If running from command line: 
    `./convert_articles.py <file_you_want_to_convert> <award_scheme>`
    e.g. `./convert_articles.py "test/131485.docx" "warc"`

# MAIN FUNCTIONS

- log_setup():
    Makes log directory and sets logger file.
    Uses 'log' for main app, lgr1 for Article Class.
- load_infile():
    Runs validation on file input by sys.argv[1].
- load_award():
    Runs validation on award input by sys.argv[2] to return correct award code from SUBS json.    
- load_json():
    Loads data from the specified json file.

# ARTICLE CLASS

- Arguments:
    IN_FILE: specify docx or html file.
    TAGS: specify tags and attributes for bleach module in json file.
    SUBS: specify substitutions for h3 headings in html.

# CLASS FUNCTIONS

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
    try:
        # infile = 'test/131478.docx'
        infile = load_infile(sys.argv[1])
        award = load_award(sys.argv[2])
        lgr.info(f'IN_FILE -> {infile}')
        lgr.info(f'award -> {award}')
        TAGS = load_json('JSON/tags.json'), 
        SUBS = load_json('JSON/subs.json')
        doc = Path(infile)
        Art = Article(
            IN_FILE=doc,
            TAGS=TAGS, 
            SUBS=SUBS,
            AWARD=award
        )
        if doc.suffix == '.docx':
            Art.convert_docx(extract_media=True)
            Art.rename_docx_images()
        elif doc.suffix == '.html':
            with open(doc, encoding='utf-8') as f:
                Art.CONTENT = f.read()
        Art.clean_html()
        Art.amend_html()#.prettify()
        Art.write_html()

    except Exception as e:
        log.error(e)

if __name__ == '__main__':
    main()
