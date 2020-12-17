# Convert Articles

A new development for automating the conversion of edited docx content to html and correctly named images. 

- **Goal:** direct cost savings for my company and reduced production time for web articles (case studies).
- We currently send this content to India and pay for a company to convert the files to html and extract all images. We then have to wait around a week for this to be completed before the article assets can be uploaded to our CMS and published as articles on our website.

Considering splitting html parsing to a utils folder to keep tidy.

### ToDo

- ~~sub h5 - h3 titles.~~ 
- ~~fix objectives h3 on WA also~~ run a check to see if any headers are missing
- ~~add Sources heading to endnotes~~
- ~~nest under an Article class~~
- ~~ensure imgs are in their own p tags~~
- regex matching for h3 titles to be more exact / account for spaces at line endings etc (or could strip()).
- ~~add requirements.txt / pip.lock to make it standalone~~
- ~~add logging~~
- ~~add file verification for sys.arv[1]~~
- ~~add unit testing: `def test_rename_docx_images(Path('test/131412/media')), IMGS={}):`~~
- remove /media folder in output path
- add warning for .emf files and tables / charts
- split hmtl amending to separate package
- use pyinstaller to make exe
- ~~allow directories as well as single docx files so doesn't start script new everytime and create new log.~~
- use colour on warnings and flags for file or dir through click cli

# Docs

# INSTRUCTIONS

If running from command line: `./convert_articles.py <file_you_want_to_convert> <award_scheme>`

- e.g. `./convert_articles.py "test/131485.docx" "warc"`

# MAIN FUNCTIONS

- log_setup():

Makes log directory and sets logger file. Uses 'log' for main app, lgr1 for Article Class.

- load_infile():

Runs validation on file input by sys.argv[1].

- load_award():

Runs validation on award input by sys.argv[2] to return correct award code from SUBS json.    

- load_json():

Loads data from the specified json file.

# ARTICLE CLASS

Arguments:

- IN_FILE: specify docx or html file.
- TAGS: specify tags and attributes for bleach module in json file.
- SUBS: specify substitutions for h3 headings in html.

# CLASS FUNCTIONS

- convert_docx(): 

Uses the pypandoc module to convert docx file to html content for parsing.    

- rename_docx_images():

Rename extracted images. Returns old img path and new img filename in a json for subtitution in html.

- clean_html():

Uses the bleach module to clean unwanted html tags and limit attributes of allowed tags. Tags and attributes are stored in json folder under '/JSON/tags.json'.

- amend_html():

Parses cleaned html content from docx, running replacements to correct headings. Heading substitutes are stored in json folder under '/JSON/subs.json'. Also contains the award code variable for inserting in `<img src""/>`.

- write_html():

Outputs cleaned and amended html content to specified file name. Pass in file name and html contents.
