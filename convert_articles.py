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
                       second_log='amend_html')

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
        self.AWARD = AWARD
        self.AWARD_CODE = SUBS[AWARD]['code']
        try:
            self.MEDIA_PATH.mkdir(exist_ok=False)
            lgr1.info(f'made dir: {self.MEDIA_PATH}')
        except FileExistsError as e:
            lgr1.debug(f'dir exists: {self.MEDIA_PATH}')
        
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
            lgr1.info('renaming images...')
            files = {p.resolve() for p in Path(path).glob(r"**/*") if p.suffix.casefold() in [".jpeg", ".jpg", ".png", ".gif", ".emf"]}
            for f in nat(files):
                ID = f.parent.parent.name # to get /<ID> rather than /media
                name = f.stem
                ext = f.suffix
                nums = [i for i in list(name) if i.isdigit()]
                num = ''.join(nums)
                n = "f" + num.zfill(2) 
                fn = f"{ID}{n}{ext}"
                fp = path / fn
                if f.parent.name == 'media':
                    try:
                        f.rename(fp)
                        lgr1.info(f'"{f.name}" --> {fn}')
                        self.IMGS.update({f.name: f"/fulltext/{self.AWARD_CODE}/images/{fn}"})
                    except FileExistsError as e:                                            # catch renaming files that are already there
                        lgr1.warning(f'img exists already: {f}')
                else:
                    self.IMGS.update({f.name: f"/fulltext/{self.AWARD_CODE}/images/{fn}"})
            lgr1.debug(f'{self.IMGS}')
            lgr1.info(f"renamed: {len(files)} images")

    def clean_html(self):
        '''
        Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags.
        Tags and attributes are stored in json folder under '/json/tags.json'.
        '''
        attrs = self.TAGS['attrs']
        tags = self.TAGS['tags']
        self.CONTENT = bleach.clean(
            self.CONTENT,
            attributes=attrs,
            tags=tags,
            strip=True
        )
        lgr1.info('cleaned html')

    def amend_html(self):
        '''
        Parses cleaned html content from docx, running replacements to correct headings.
        Heading substitutes are stored in json folder under '/json/subs.json'.
        Also contains the award code variable for inserting in <img src""/>.
        '''
        tree = Soup(self.CONTENT, "html.parser")

        def wrap_img(ig):
            '''Wraps img in p tags.'''
            ig.wrap(tree.new_tag('p'))
            lgr2.info(f'wrapped ^^^')

        def space_tag(tag):
            '''Spaces a tag with newlines before and after.'''
            try:
                tag.insert_before('\n')                      
                tag.insert_after('\n')
            except NotImplementedError as e:
                lgr2.warning(f"couldn't space tag: {tag}")

        def html_images():
            '''If images exist, replace the source attribute to renamed image and ensre wrapped in <p> tags.'''
            images = tree.find_all('img')
            lgr2.debug(f"article images: {images}")
            if images:
                for ig in images:
                    try:
                        src = ig['src']
                        for k, v in self.IMGS.items():
                            if k in src:
                                ig['src'] = src.replace(src, v)
                                lgr2.info(f'<img src="{k}"> --> <img src="{v}">')
                    except KeyError as e:
                        lgr2.warning('img caught key error')
                        lgr2.debug(e)
                    try:
                        prt = ig.parent
                        if ig.parent.name == 'p':
                            space_tag(prt)
                            prt.insert_after(ig)                                # insert all images outside of p tag to wrap them properly in p tags.
                            wrap_img(ig)
                            if len(prt.get_text(strip=True)) == 0:              # strip whitespace and remove p tag if empty
                                prt.unwrap()
                                lgr2.info(f'cut {prt}')
                            # space_tag(ig)
                        else:
                            space_tag(ig)
                            wrap_img(ig)
                    except ValueError as e:
                        lgr2.warning('img caught value error')
                        lgr2.debug(e)
            else:
                lgr2.info('no images...')

        def html_headers_unify():
            '''Makes all headers <p><strong>.'''
            headers = tree.find_all(['h1','h2', 'h3','h4','h5'])
            if not headers:
                lgr2.info('no header tags to replace...')
            else:
                for hdr in headers:
                    if hdr:
                        hdr.string.wrap(tree.new_tag('strong'))
                        hdr.name = 'p'
                        lgr2.debug(f'header --> {hdr}')
            # match all p tags with bold and check punctuation endings to filter bold sentences from subheadings in h5
            lgr2.info('changing all subheadings to h5...')
            paras = tree.find_all('p')
            for p in paras:
                if p.find('strong'):
                    if p.text.endswith((".",",",":",";","?")):      # regex this
                        pass
                    else:
                        p.strong.unwrap()
                        p.name = 'h5'
                        lgr2.debug(f'<p><strong> --> {p}')

        def html_headers_replace():
            '''Runs replacements on headers.'''
            replace = {                                             # merge award specific headers
                **self.SUBS[self.AWARD],                            # with generic headers
                **self.SUBS['All']
            }
            lgr2.info('changing award subheadings to h3...')
            h5s = tree.find_all('h5')          
            for h5 in h5s:
                space_tag(h5)
                for k, v in replace.items():        
                    if h5.text.casefold().strip() in v.casefold():
                        h5.name = 'h3'
                        lgr2.debug(f'<h5> --> {h5}')
            
        def html_lists():
            for li in tree.find_all('li'):
                if li.find('p'):
                    li.p.unwrap()
                    # lgr2.info(f'<li><p> --> {li}') # unicode error printing these in logs

        html_images()
        html_headers_unify()
        html_headers_replace()
        html_lists()
        self.CONTENT = tree

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
    f = Path(infile)
    log.debug(f'infile argument: {f}')
    if f.is_file():
        log.info(f'file -> {f}')
        return f
    else:
        log.warning(f'{f} not a valid file')
        raise SystemExit

def load_award(a, SUBS):
    '''
    Runs validation on award input by sys.argv[2] to return correct award code from SUBS json.
    '''
    log.debug(f'award argument: {a}')
    keys = [*SUBS.keys()]                                           # unpacks keys into list                 
    keys.remove('All')                                              # keep only award sections of subs.json    
    for k in filter(lambda k: a.casefold() in k.casefold(), keys):  # casefold to match case
        award = k
        log.info(f'award -> {award}')
        return award
    else:
        log.warning(f'{a} not a valid award')
        raise SystemExit

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
        TAGS = load_json('JSON/tags.json') 
        SUBS = load_json('JSON/subs.json')
        try:
            infile = load_infile(sys.argv[1])
            award = load_award(a=sys.argv[2], SUBS=SUBS)
        except IndexError as e:
            log.debug('no sys args')
            infile = "test/131412.docx"#"c:/Users/arondavidson/OneDrive - Ascential/Desktop/Murkies WPA&WMA/Aron WARC Awards/131412.docx"##input('path to file: # e.g. "test/131470.docx"\n')
            award = input('award: # e.g. "warc" "mena" "asia" "media"\n')
            infile = load_infile(infile=infile)
            award = load_award(a=award, SUBS=SUBS)
        Art = Article(
            IN_FILE=infile,
            TAGS=TAGS, 
            SUBS=SUBS,
            AWARD=award
        )
        if infile.suffix == '.docx':
            Art.convert_docx(extract_media=True)
            Art.rename_docx_images()
        elif infile.suffix == '.html':
            with open(infile, encoding='utf-8') as f:
                Art.CONTENT = f.read()
        Art.clean_html()
        Art.amend_html()#.prettify()
        Art.write_html()

    except AttributeError as e:
        lgr1.warning(e)
    except Exception as e:
        log.error(e)
        raise e

if __name__ == '__main__':
    main()
