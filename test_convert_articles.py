import unittest
import convert_articles as CA
from pathlib import Path
from pprint import pprint

TAGS = {
	"tags": [
	    "img","h1","h2", "h3","h4","h5","br",
	    "b", "strong", "em", "i", "u", "a", "p",
	    "ul", "li", "ol", "sup"
	],
	"attrs": {
	    "a": ["href"],
	    "img": ["src","alt"],
	    "ul": ["start"],
	    "ol": ["start"]
    }
}
SUBS = {}

class TestArticleFunctions(unittest.TestCase):

	def test_load_infile(self):
		f = CA.load_infile('test/131412.docx')
		self.assertTrue(f)
	
	def test_load_award(self):
		a = CA.load_award('warc')
		self.assertTrue(a)

	def test_load_json(self):
		s = CA.load_json('JSON/subs.json')
		t = CA.load_json('JSON/tags.json')
		self.assertTrue(len(s) > 0 and len(t) > 0)
		# return pprint(data['WARC Awards'], indent=4)
	

	def test_rename_docx_images(self):
		pass
		# result = CA.rename_docx_images(Path('test/131412'), IMGS={})
		# self.
		# return print(result)

	def test_convert_docx(self):
		# file = r'T:\Ascential Events\WARC\Backup Server\Loading\Monthly content for Newgen\Project content - September 2020\Media Awards 2020\editors papers\dupes\shortlisted\134211.docx'
		# contents, media = CA.convert_docx(
		# 	file=Path(file), extract_media=False)
		pass

	def test_clean_html(self):
		# file = 'test/test0.html'
		# with open(file, 'r', encoding='utf-8') as f:
		# 	html = f.read()
		# contents = CA.clean_html(html, TAGS)
		# print(contents)
		# self.assertTrue('<h5>' in contents)
		pass

	def test_amend_html(self):
		pass
		# file = 'test/test0.html'
		# with open(file, 'r', encoding='utf-8') as f:
		# 	html = f.read()
		# html = CA.clean_html(html, TAGS)
		# contents = CA.amend_html(html, SUBS)
		# print(contents)
		# self.assertTrue('<h5>' in contents)

	def test_write_html(self):
		pass

	def test_main(self):
		pass


if __name__ == '__main__':
	unittest.main()