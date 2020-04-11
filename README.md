## Warning!
currently some features are not working, esspecially blanks not :(, fix will come

## Big News
I am currently rewriting the app in Rust.

# stuPDF
A commandline tool for PDF manipulation, with slicing and multiplying features*.

Download python or the exe file if you have not python installed.

The follwing modes are available:
- blanks: automatically adds blank pages to a pdf
- blank: add blank pages to specified pages
- insert: insert a page, similar to blank
- split: split pdf files
- merge: merges pdfs
- rotate: rotates pdf
- cute: experimental, puts two 2 pages onto one (rotated)
- delete: deletes specified pages
- overlay: overlays pages with others
- shuffle: shuffles pdf
- zip: zips several pdfs
- meta: changes metavariables
- info: displays info about pdf

*slicing: only part of the pdf is inputed if using python like slices, as here: "shakespear.pdf[3:90:5]"
          
*multiplying: "split_{0:3}.pdf" equals "split_0.pdf split_1.pdf split_2.pdf"

I plan to also add:
- cutebook: similar to cute, but aranges pages such that folded results in a book
