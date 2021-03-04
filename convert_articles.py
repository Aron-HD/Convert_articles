#! /usr/bin/env python
import logging as log
import os
import sys
import json
import bleach
import pypandoc
import subprocess
from bs4 import BeautifulSoup as Soup
from natsort import natsorted as nat
from datetime import datetime
from pathlib import Path
from glob import glob


def resource_path(relative_path):
    '''Get absolute path to resource, works for dev and for PyInstaller.'''
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
    # base_path = Path(__file__).parent
    # return (base_path / relative_path).resolve()


def log_setup(
    first_log,      # name of logger for section of project e.g. 'Article class'
    second_log      # second logger section e.g. 'amend_html'
):
    '''
    Makes log directory and sets logger file.
    Uses 'log' for main app, lgr1 for Article Class.
    '''
    fd = 'logs'                                                     # folder name
    # log directory
    ld = Path(__file__).parent / fd
    # ensure exists
    ld.mkdir(exist_ok=True)
    fn = Path(__name__).with_suffix(
        '.log')                         # app filename
    # path for log file
    lp = fd + '/%d_%m_%Y - (%H-%M-%S) - ' + f'{fn}'
    # log name formatted
    nm = datetime.now().strftime(lp)
    log.basicConfig(
        # set up logging to file
        level=log.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        handlers=[log.FileHandler(nm, 'w', 'utf-8')]
        # filename=nm,
        # filemode='w',
    )

    # set a simpler format for console
    fm = log.Formatter('%(name)-12s: %(levelname)-8s > %(message)s')
    # define a Handler as console
    cs = log.StreamHandler()
    # write INFO messages or higher to the sys.stderr
    cs.setLevel(log.INFO)
    # tell the handler to use this format
    cs.setFormatter(fm)
    # add the handler to the root logger
    log.getLogger('').addHandler(cs)

    # Define loggers for different areas of application
    lgr1 = log.getLogger(first_log)
    # trag where stuff is happening in logs
    lgr2 = log.getLogger(second_log)
    lgr1.debug(f'defined lgr1: {lgr1}')
    lgr2.debug(f'defined lgr2: {lgr2}')
    # log to root
    log.debug('setup logging')
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

    def __init__(
        self,
        IN_FILE,  # user input filename
        TAGS,     # allowed html tags and attributes for bleach module
        SUBS,     # substitute awards headers, also loaded in from JSON
        AWARD     # user input award - warc / media / mena / asia
    ):
        # super(Article, self).__init__()
        content = None  # html content variable to update\\\\\\\\\\\\\\\\\\\\\\
        self.IMGS = {}  # image names for renaming passed in when extracted from docx
        self.TAGS = TAGS
        self.SUBS = SUBS
        self.AWARD = AWARD
        self.IN_FILE = IN_FILE
        # award-specific code to go in img src tags
        self.AWARD_CODE = SUBS[AWARD]['code']
        # path for extracting docximages to
        self.MEDIA_PATH = IN_FILE.parent / 'htm'
        self.OUT_FILE = Path(f"{self.MEDIA_PATH}/{IN_FILE.stem}.htm")
        try:
            # ensure directory for img / htm extraction exists
            self.MEDIA_PATH.mkdir(exist_ok=False)
            lgr1.info(f'made dir: {self.MEDIA_PATH}')
        except FileExistsError as e:
            lgr1.debug(f'dir exists: {self.MEDIA_PATH}')

    def convert_docx(
        self,
        extract_media=True  # default extract images from docx, toggle false if don't want images
    ):
        '''
        Uses the pypandoc module to convert docx file to html content for parsing and extracts images.
        '''
        if extract_media:
            lgr1.info('converting docx to html and extracting images...')
            extra_args = [f'--extract-media={self.MEDIA_PATH}']
        else:
            lgr1.info('converting docx to html...')
            extra_args = []
        # find a way to extract to same folder rather than 'ID/media'
        content = pypandoc.convert_file(
            str(self.IN_FILE), 'html5', extra_args=extra_args)
        return content

    @staticmethod
    def image_cleanup(image):
        '''
        Convert images that are tiff, tif or emf to jpgs.
        '''
        new_img = image.with_suffix('.jpg')
        cmd = ['magick', str(image), str(new_img)]
        subprocess.call(cmd, shell=True)
        lgr1.info(f"converted: '{image.name}' --> '{new_img.name}'")
        return None

    def rename_docx_images(self):
        '''
        Rename extracted images.
        Returns old img path and new img filename in a dict for subtitution in html.
        '''
        path = self.MEDIA_PATH
        ID = self.OUT_FILE.stem  # f.parent.parent.name # to get /<ID> rather than /media
        lgr1.debug(f'ID = {ID}')
        lgr1.info('renaming images...')
        files = {p.resolve() for p in Path(path).glob(r"**/image*") if p.suffix.casefold()
                 in [".jpeg", ".jpg", ".png", ".gif", ".emf", ".tiff", ".tif"]}
        if not files:
            lgr1.info('no images to rename')
        else:
            for f in nat(files):
                name = f.stem
                ext = f.suffix
                nums = [i for i in list(name) if i.isdigit()]
                num = ''.join(nums)
                n = "f" + num.zfill(2)
                fn = f"{ID}{n}{ext}"
                fp = path / fn
                lgr1.debug(fp)
                if f.parent.name == 'media':
                    try:
                        # convert unwanted images
                        if f.suffix.endswith(('.emf', '.tiff', '.tif')):
                            self.image_cleanup(f)
                            # change extension to jpg
                            fn = fn.replace(ext, '.jpg')
                            fp = path / fn
                        f.rename(fp)
                        lgr1.debug(f'"{f.name}" --> {fn}')
                        self.IMGS.update({f.name: f"/fulltext/{self.AWARD_CODE}/images/{fn}"})
                    # catch renaming files that are already there
                    except FileExistsError as e:
                        lgr1.warning(f'img exists already: {f}')
                else:
                    self.IMGS.update({f.name: f"/fulltext/{self.AWARD_CODE}/images/{fn}"})
            lgr1.debug(f'{self.IMGS}')
            lgr1.info(f"renamed: {len(self.IMGS)} images")

    def clean_html(self, content):
        '''
        Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags.
        Tags and attributes are stored in json folder under '/json/tags.json'.
        '''
        content = bleach.clean(
            content,
            attributes=self.TAGS['attrs'],
            tags=self.TAGS['tags'],
            strip=True
        )
        lgr1.info('cleaned html')
        return content

    def amend_html(self, content):
        '''
        Parses cleaned html content from docx, running replacements to correct headings.
        Heading substitutes are stored in json folder under '/json/subs.json'.
        Also contains the award code variable for inserting in <img src""/>.
        '''

        def wrap_img(tag):
            '''Wraps img in p tags.'''
            tag.wrap(tree.new_tag('p'))
            lgr2.debug(f'wrapped ^^^')

        def space_tag(tag):
            '''Spaces a tag with newlines before and after.'''
            try:
                tag.insert_before('\n')
                tag.insert_after('\n')
            except NotImplementedError as e:
                lgr2.warning(f"couldn't space tag: {tag}")

        def amend_images(tree):
            '''If images exist, replace the source attribute to renamed image and ensure in its own paragraph.'''
            images = tree.find_all('img')
            lgr2.debug(f"article images: {images}")
            if images:
                for ig in images:
                    try:
                        src = ig['src']
                        for k, v in self.IMGS.items():
                            if k in src:
                                # set original <img src=""> attribute to new variable
                                ig['src'] = src.replace(src, v)
                                lgr2.debug(f'<img src="{k}"> --> <img src="{v}">')
                    except KeyError as e:
                        lgr2.error('img caught key error')
                        lgr2.debug(e)
                    try:
                        prt = ig.parent
                        if ig.parent.name == 'p':
                            space_tag(prt)
                            # insert all images outside of p tag to wrap them properly in p tags.
                            prt.insert_after(ig)
                            wrap_img(ig)
                            # strip whitespace and remove p tag if empty
                            if len(prt.get_text(strip=True)) == 0:
                                prt.unwrap()
                                lgr2.debug(f'cut {prt}')
                            # space_tag(ig)
                        else:
                            space_tag(ig)
                            wrap_img(ig)
                    except ValueError as e:
                        lgr2.error('img caught value error')
                        lgr2.debug(e)
            else:
                lgr2.debug('no images...')

        def amend_headers_unify(tree):
            '''Makes all headers bold paragraphs.'''
            headers = tree.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            if not headers:
                lgr2.debug('no header tags to replace...')
            else:
                for hdr in headers:
                    if hdr:
                        hdr.string.wrap(tree.new_tag('strong'))
                        hdr.name = 'p'
                        lgr2.debug(f'header --> {hdr}')
            # match all p tags with bold and check punctuation endings to filter bold sentences from subheadings in h5
            lgr2.debug('changing all subheadings to h5...')
            paras = tree.find_all('p')
            for p in paras:
                if p.find('strong'):
                    if p.text.endswith((".", ",", ":", ";", "?")):      # regex this
                        pass
                    else:
                        p.strong.unwrap()
                        p.name = 'h5'
                        lgr2.debug(f'<p><strong> --> {p}')

        def amend_headers_replace(tree):
            '''Runs replacements on headers.'''
            replace = {                                             # merge award specific headers
                # with generic headers
                **self.SUBS[self.AWARD],
                **self.SUBS['All']
            }
            lgr2.debug('changing award subheadings to h3...')
            h5s = tree.find_all('h5')
            for h5 in h5s:
                space_tag(h5)
                for k, v in replace.items():
                    if h5.text.casefold().strip().replace("’", "'") == v.casefold():  # replace apostrophe to match Client's view
                        h5.name = 'h3'
                        lgr2.debug(f'<h5> --> {h5}')

        def amend_lists(tree):
            '''Removes paragraph tags within list elements.'''
            lgr2.debug('checking list elements...')
            for li in tree.find_all('li'):
                if li.find('p'):
                    li.p.unwrap()
                    lgr2.debug(f'<li><p> --> {li}')

        def amend_footnotes(tree):
            '''Removes anchor tags from footnotes and endnotes section and adds h3 header to endnotes.'''
            lgr2.debug('amending footnotes...')
            ftn = tree.find(role="doc-backlink")
            if ftn:
                h3 = tree.new_tag('h3')
                h3.string = 'Sources'
                # add <h3>Sources</h3> if endnotes exist
                ftn.parent.parent.insert_before(h3)
                h3.insert_after('\n')
                lgr2.debug(f'{h3} <-- inserted before {ftn.parent.parent.name}')

                for a in tree.find_all('a'):
                    if a.has_attr('role'):
                        if a['role'] == 'doc-noteref':
                            sup = a.find('sup')
                            if sup:
                                a.unwrap()                          # unwrap to leave sup tag and contents intact
                                lgr2.debug(f'{a} --> {sup}')
                        elif a['role'] == 'doc-backlink':
                            lgr2.debug(f'deleting tag --> {a}')
                            a.decompose()                           # removes the backlink entirely '<a>↩︎</a>'
            else:
                lgr2.debug('no footnotes..')

        tree = Soup(content, "html.parser")
        amend_images(tree)
        amend_headers_unify(tree)
        amend_headers_replace(tree)
        amend_lists(tree)
        amend_footnotes(tree)
        return tree

    def write_html(self, content):
        '''
        Outputs cleaned and amended html content to specified file name.
        Pass in file name and html contents.
        '''
        f = self.OUT_FILE
        with open(f, 'w', encoding='utf-8') as f:
            f.write(str(content))
            lgr1.info(f'wrote file -> {f.name}')


def load_infile(infile):
    '''
    Runs validation on file input by sys.argv[1].
    '''
    f = Path(infile)
    log.debug(f'infile argument: {f}')
    if f.is_file():
        log.info(f'file -> {f}')
        return f
    if f.is_dir():
        log.info(f'directory -> {f}')
        return f
    else:
        log.warning(f'{f} not a valid file')
        raise SystemExit


def load_award(a, SUBS):
    '''
    Runs validation on award input by sys.argv[2] to return correct award code from SUBS json.
    '''
    log.debug(f'award argument: {a}')
    # unpacks keys into list
    keys = [*SUBS.keys()]
    # keep only award sections of subs.json
    keys.remove('All')
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
        with open(resource_path(file)) as f:
            data = json.load(f)
            return data
    except Exception as e:
        log.error('error loading json:', e)


def process(infile, TAGS, SUBS, award):
    Art = Article(
        IN_FILE=infile,
        TAGS=TAGS,
        SUBS=SUBS,
        AWARD=award
    )
    if infile.suffix == '.docx':
        content = Art.convert_docx(extract_media=True)
        Art.rename_docx_images()
    elif infile.suffix == '.html':
        with open(infile, encoding='utf-8') as f:
            content = f.read()
    cleaned = Art.clean_html(content)
    amended = Art.amend_html(cleaned)  # .prettify()
    Art.write_html(amended)


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
            infile = input('file path:\n - ')
            award = input('select award - "warc" "mena" "asia" "media":\n - ')
            infile = load_infile(infile=infile)
            award = load_award(a=award, SUBS=SUBS)

        if infile.is_dir():
            for f in infile.glob(r'*.docx'):
                process(f, TAGS, SUBS, award)
        else:
            process(infile, TAGS, SUBS, award)
        log.info('# FINISHED #')
        # input('hit any key to exit:')

    except AttributeError as e:
        lgr1.warning(e)
    except Exception as e:
        log.error(e)
        raise e


if __name__ == '__main__':
    main()
