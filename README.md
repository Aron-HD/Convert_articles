# Convert Articles

A new development for automating the conversion of edited docx content to html and correctly named images. 

- **Goal:** direct cost savings for my company and reduced production time for web articles (case studies).
- We currently send this content to India and pay for a company to convert the files to html and extract all images. We then have to wait around a week for this to be completed before the article assets can be uploaded to our CMS and published as articles on our website.

Considering nesting these functions under an Article class.

## Docs

##### INSTRUCTIONS

- If running from command line: 
- `./convert_articles.py <file_you_want_to_convert>`

##### FUNCTIONS

- extract_docx_images():

Runs bash shell script to unzip and rename images.
Returns old img path and new img filename in a json for subtitution in html.

- convert_docx(): 

Uses the pypandoc module to convert docx file to html content for parsing.    

- load_json():

Loads data from the specified json file.
Must give both arguments: <folder path>, <file>.

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
