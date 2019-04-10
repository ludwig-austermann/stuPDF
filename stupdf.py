# Ludwig Austermann
# stuPDF
# visit www.github.com/ludwig-austermann to view the project

#personal fave: stupdf blanks <input file> -sep 1 -s <end index> -e <biblio> -t 160 -cwb
# PyInstaller stupdf.py -F -n stuPDF
import PyPDF2, argparse, random, itertools

VERSION = '0.6.0'

argparse.ArgumentParser.exit_after_cmd = True
normal_behaviour = True
def nexit(self, status=0, message=None):
    global normal_behaviour
    if message:
        self._print_message(message, argparse._sys.stderr)
        normal_behaviour = False
    if self.exit_after_cmd:
        argparse._sys.exit(status)
argparse.ArgumentParser.exit = nexit


class Range:
    def __init__(self, s=''):
        if s:
            self.all = False
            l = s.split(':')
            if len(l) > 1:
                self.range = range(*[int(i) for i in l])
            else:
                temp = int(l[0])
                self.range = range(temp, temp+1)
        else:
            self.all = True

    def __contains__(self, item):
        return self.all or item in self.range

    def __iter__(self):
        return itertools.count if self.all else iter(self.range)

    def __len__(self):
        return 0 if self.all else len(self.range)


class Ranges:
    def __init__(self, l=[]):
        self.list = l
        self.all = not l or any(e.all for e in l)
        if not self.all:
            self.values = sorted(set(itertools.chain(*(i.range for i in l))))

    @classmethod
    def from_str(cls, s=''):
        '''if s="" means to use all possible values'''
        return Ranges([Range(r) for r in s.split(',')])

    def __contains__(self, item):
        return self.all or item in self.values

    def __iter__(self):
        return itertools.count if self.all else iter(self.values)

    def __len__(self):
        return 0 if self.all else len(self.values)


class CropFile:
    def __init__(self, s):
        l = s.split('[')
        self.filename = l[0]
        self.file = None
        if len(l) > 1:
            self.ranges = Ranges.from_str(l[1].split("]")[0]) # [4:60:3,100:120]
        else:
            self.ranges = Ranges()

    def __iter__(self): # return the pages, ensure that opened first
        #return itertools.compress(self.file.pages, self.ranges)
        if self.ranges.all:
            return iter(self.file.pages)
        else:
            maxpage = self.file.getNumPages()
            return (self.file.getPage(page) for page in self.ranges if page < maxpage)

    def inf_iter(self):
        return itertools.cycle(self)

    def _open_file(self, start='', end=''):
        self.file = PyPDF2.PdfFileReader(open(f'{start}{self.filename}{end}', 'rb'))

    def start(self, start='', end=''):
        self._open_file(start, end)
        return self

    def __len__(self):
        return len(self.ranges)

class CropFiles: #! add functions and impl
    def __init__(self, s=''):
        l = s.split('{')
        self.before = l[0]
        if len(l) > 1:
            self.expand = True
            self.slicer = l[1].split('}')[0]
            self.after = s.split('}')[1]
        else:
            self.expand = False

    def start(self, start='', end='', formater_len=0):
        if self.expand:
            self.list = [CropFile(f'{self.before}{v:0{formater_len}}{self.after}').start(start, end) for v in Range(self.slicer)]
        else:
            self.list = [CropFile(self.before).start(start, end)]
        return self.list

    @classmethod
    def start_list(cls, l, start='', end='', formater_len=0):
        return itertools.chain(*[v.start(start, end, formater_len) for v in l])


def calc_blanks(pdf, total, _slice=0): # if _slice=0 _slice := pdf
    return max(_slice // (total - pdf), 1)


def save(pdf, args):
    with open(args.output + args.autoAddPdf, 'wb') as file: # saving
        pdf.write(file)

    print(f'Done, pdf saved as "{args.output}{args.autoAddPdf}".')


def writer_iter(write_pdf, read_pdf, slicer):
    for i, page in enumerate(read_pdf):
        if i in slicer:
            yield page
        else:
            write_pdf.addPage(page)


def blanks(args):
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()
    sty_pdf = args.blankPageStyle.start(end=args.autoAddPdf) if args.blankPageStyle else None

    if sty_pdf:
        sty_iter = sty_pdf.inf_iter()

    sep = args.seperate if args.seperate else calc_blanks(len(read_pdf), args.total, len(args.slice))
    num = args.blanksnum if not args.allowMoreBlanks else (args.total - read_pdf.numPages) // (read_pdf.numPages - args.start) #! recalculate

    for i, page in enumerate(writer_iter(write_pdf, read_pdf, args.slice)):
        write_pdf.addPage(page)

        if args.nonregular: # if user wants to recalculate sep
            sep = calc_blanks(len(read_pdf) - i, args.total - i, len(args.slice))

        if sep and not i % sep: # insertion of blankpages
            for _ in range(num):
                if sty_pdf:
                    write_pdf.addPage(next(sty_iter))
                else:
                    write_pdf.addBlankPage()

    if args.total < write_pdf.getNumPages(): #warning message if too many pages
        print(f'Warning, more pages ({write_pdf.getNumPages()}) than total ({args.total}).')

    if args.completeWithBlanks: #completition to total
        for _ in range(args.total - write_pdf.getNumPages()):
            if sty_pdf:
                write_pdf.addPage(next(sty_iter))
            else:
                write_pdf.addBlankPage()

    save(write_pdf, args)


def insert(args):
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()

    pages = Ranges(args.pages)

    if args.insertfile != '_':
        ins_iter = args.insertfile.start(end=args.autoAddPdf).inf_iter()

    for i, page in enumerate(read_pdf):
        write_pdf.addPage(page)
        if i in pages:
            if args.insertfile == '_':
                write_pdf.addBlankPage()
            else:
                write_pdf.addPage(next(ins_iter))

    save(write_pdf, args)


def splitter(args):
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdfs = [PyPDF2.PdfFileWriter()]

    pages = Ranges(args.splitPages)

    for i, page in enumerate(read_pdf):
        if i in pages:
            write_pdfs.append(PyPDF2.PdfFileWriter())
        write_pdfs[-1].addPage(page)

    for i, wpdf in enumerate(write_pdfs):
        with open(f'{args.outputPrefix}{i}.pdf', 'wb') as file: #saving
            wpdf.write(file)

    print(f'Done, saved files {args.outputPrefix}0.pdf to {args.outputPrefix}{len(write_pdfs) - 1}.pdf.')


def merger(args):
    merger_pdf = PyPDF2.PdfFileWriter()

    for pdf in CropFiles.start_list(args.inputs, args.inputPrefix, args.autoAddPdf, args.formaterPlaceholderLength):
        for page in pdf:
            merger_pdf.addPage(page)

    save(merger_pdf, args)


def rotate(args):
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()

    pages = Ranges(args.pages)

    for i, page in enumerate(read_pdf):
        if i in pages:
            write_pdf.addPage(page.rotateCounterClockwise(args.angle))
        else:
            write_pdf.addPage(page)

    save(write_pdf, args)


def cute(args): pass
"""
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()

    for i in range(0, len(read_pdf), 2):
        read_pdf.getPage(i).rotateCounterClockwise(90).scaleBy(0.5)
        read_pdf.getPage(i + 1).rotateCounterClockwise(90).scaleBy(0.5)
        read_pdf.getPage(i).mergePage(read_pdf.getPage(i + 1))
        write_pdf.addPage(read_pdf.getPage(i))

    if read_pdf.numPages & 1:
        #write_pdf.addPage()
        pass

    save(write_pdf, args) """ #! needs 0.5 and proper code


def delete(args):
    read_pdf = args.input.start(end=args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()

    pages = Ranges(args.pages)

    for i, page in enumerate(read_pdf):
        if i not in pages:
            write_pdf.addPage(page)

    save(write_pdf, args)


def overlay(args): #! doesn't work
    read_pdf, *pdfs = CropFiles.start_list(args.inputs, args.inputPrefix, args.autoAddPdf, args.formaterPlaceholderLength)
    #read_pdf = args.inputs[0].start(args.inputPrefix, args.autoAddPdf)
    write_pdf = PyPDF2.PdfFileWriter()
    #pdfs = []

    #for pdf in args.inputs[1:]:
    #    pdfs.append(pdf.start(args.inputPrefix, args.autoAddPdf))

    for i, page in enumerate(read_pdf):
        for pdf in pdfs:
            if i >= len(pdf):
                continue
            page.mergePage(pdf.file.getPage(i))
        write_pdf.addPage(page)

    save(write_pdf, args)


def shuffle(args):
    shuf = list(args.input.start(end=args.autoAddPdf))
    random.shuffle(shuf)
    write_pdf = PyPDF2.PdfFileWriter()

    for page in shuf:
        write_pdf.addPage(page)

    save(write_pdf, args)


def newzip(its, ns):
    if not ns:
        ns = [1] * len(its)
    cont = 1
    while cont:
        cont = 0
        for it, n in zip(its, ns):
            for _ in range(n):
                try:
                    yield next(it)
                    cont = 1
                except StopIteration: pass


def zipping(args):
    write_pdf = PyPDF2.PdfFileWriter()
    #pdfs = []
    pdfs_iters = [iter(v) for v in CropFiles.start_list(args.inputs, args.inputPrefix, args.autoAddPdf, args.formaterPlaceholderLength)]

    #for pdf in args.inputs:
    #    pdfs.append(iter(pdf.start(args.inputPrefix, args.autoAddPdf)))

    for page in newzip(pdfs_iters, args.ratios):
        write_pdf.addPage(page)

    save(write_pdf, args)


def info(args):
    info_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, 'rb'))

    for i in info_pdf.documentInfo:
        print(f'{i:{20}}:\t{info_pdf.documentInfo[i]}')
    print(f'pages               :\t{info_pdf.numPages}')
    print(f'outlines            :\t{info_pdf.outlines}')
    print(f'page layout         :\t{info_pdf.pageLayout}')
    print(f'page mode           :\t{info_pdf.pageMode}')
    print(f'encrypted           :\t{info_pdf.isEncrypted}')
    print(f'xmpMetadata         :\t{info_pdf.xmpMetadata}')


parser = argparse.ArgumentParser(description='A simple solution inserting blank pages into an existing pdf but also those standard features like splitting, merging, etc.', epilog='You can easily contribute to the project. More infos on version.')
parser.add_argument('-pdf', '--autoAddPdf', help='automatically adds .pdf to files', action='store_const', const='.pdf', default='')
parser.add_argument('-v', '--version', action='version', version=f'stupdf {VERSION}  \nContribute to the project on github:  \ngithub.com/austermann  \nchangelog: added insert and blank function  \ncode cleanup  \nuse open stuPDF without terminal  \ncompletely rewritten, bugfixes and [k:l:i,m:n:j,...] expressions  \nadded <curcly bracket>1:6<curcly bracket> expressions as "multiplyers"')
subparsers = parser.add_subparsers()
###BLANKS###
blanks_parser = subparsers.add_parser('blanks')
blanks_parser.add_argument('input', help='input pdf', type=CropFile)
blanks_parser.add_argument('-o', '--output', help='output pdf', default='blanks.pdf')
blanks_parser.add_argument('-sep', '--seperate', help='insert every sep pages the blank page', type=int)
blanks_parser.add_argument('-s', '--slice', help='slice of document to operate on, total still uses whole document', default=0, type=Range)
blanks_parser.add_argument('-t', '--total', help='total pages of output, if no sep, calculates sep itself', default=0, type=int)
exbla = blanks_parser.add_argument_group('extra options', 'using pro features')
exbla.add_argument('-num', '--blanksnum', help='number of blank pages per sep', default=1, type=int)
exbla.add_argument('-cwb', '--completeWithBlanks', action='store_true')
exbla.add_argument('-amb', '--allowMoreBlanks', action='store_true')
exbla.add_argument('-nreg', '--nonregular', help='calculates pages every loop', action='store_true')
exbla.add_argument('-style', '--blankPageStyle', help='pdf giving "blank" pages', type=CropFile)
blanks_parser.set_defaults(func=blanks)
###BLANK###
blank_parser = subparsers.add_parser('blank')
blank_parser.add_argument('input', help='input pdf', type=CropFile)
blank_parser.add_argument('-p', '--pages', help='pages, where to insert', nargs='+', default=0, type=Range)
blank_parser.add_argument('-o', '--output', help='output pdf', default='blank.pdf')
blank_parser.set_defaults(func=insert, insertfile='_')
###INSERT###
insert_parser = subparsers.add_parser('insert')
insert_parser.add_argument('input', help='input pdf', type=CropFile)
insert_parser.add_argument('insertfile', help='insert pdf, if "_" inserts blanks', type=CropFile)
insert_parser.add_argument('-p', '--pages', help='pages, where to insert (for: page x to page y every ith use: x:y:i )', nargs='+', default=0, type=Range)
insert_parser.add_argument('-o', '--output', help='output pdf', default='insert.pdf')
insert_parser.set_defaults(func=insert)
###SPLIT###
split_parser = subparsers.add_parser('split')
split_parser.add_argument('input', help='input pdf', type=CropFile)
split_parser.add_argument('splitPages', help='pages, where to split (for: page x to page y every ith use: x:y:i )', nargs='+', type=Range)
split_parser.add_argument('-o', '--outputPrefix', help='outputs prefix', default='split_')
split_parser.set_defaults(func=splitter)
###MERGE###
merge_parser = subparsers.add_parser('merge')
merge_parser.add_argument('inputs', help='input files (file1[x:y:i] ...: uses only every ith page from x to y for file1)', nargs='+', type=CropFiles)
merge_parser.add_argument('-o', '--output', help='output pdf', default='merge.pdf')
merge_parser.add_argument('-i', '--inputPrefix', help='adds prefix to all input pdf names', default='')
merge_parser.add_argument('-fn', '--formaterPlaceholderLength', help='display maximum numbers up to 10^fn properly', default=0, type=int)
merge_parser.set_defaults(func=merger)
###ROTATE###
rotate_parser = subparsers.add_parser('rotate')
rotate_parser.add_argument('input', help='input pdf', type=CropFile)
rotate_parser.add_argument('angle', help='angle to rotate the pdf (counterclockwise in degrees)', default=90, type=int)
rotate_parser.add_argument('-o', '--output', help='output pdf', default='rotate.pdf')
rotate_parser.add_argument('-p', '--pages', help='only selected pages (for: page x to page y every ith use: x:y:i )', nargs='*', type=Range)
rotate_parser.set_defaults(func=rotate)
###CUTE###
cute_parser = subparsers.add_parser('cute', description='Transform a pdf to one with two pages per page.')
cute_parser.add_argument('input', help='input pdf', type=CropFile)
cute_parser.add_argument('-o', '--output', help='output pdf', default='cute.pdf')
cute_parser.set_defaults(func=cute)
###DELETE###
delete_parser = subparsers.add_parser('delete')
delete_parser.add_argument('input', help='input pdf', type=CropFile)
delete_parser.add_argument('pages', help='pages to delete (for: page x to page y every ith use: x:y:i )', nargs='+', type=Range)
delete_parser.add_argument('-o', '--output', help='output pdf', default='delete.pdf')
delete_parser.set_defaults(func=delete)
###OVERLAY###
overlay_parser = subparsers.add_parser('overlay')
overlay_parser.add_argument('inputs', help='input pdfs (file1[x:y:i] ...: uses only every ith page from x to y for file1)', nargs='+', type=CropFiles)
overlay_parser.add_argument('-o', '--output', help='output pdf', default='overlay.pdf')
overlay_parser.add_argument('-i', '--inputPrefix', help='adds prefix to all input pdf names', default='')
overlay_parser.add_argument('-fn', '--formaterPlaceholderLength', help='display maximum numbers up to 10^fn properly', default=0, type=int)
overlay_parser.set_defaults(func=overlay)
###SHUFFLE###
shuffle_parser = subparsers.add_parser('shuffle')
shuffle_parser.add_argument('input', help='input pdf', type=CropFile)
shuffle_parser.add_argument('-o', '--output', help='output pdf', default='shuffle.pdf')
shuffle_parser.add_argument('-s', '--slice', help='not implemented yet', type=Range) #! not impl yet
shuffle_parser.set_defaults(func=shuffle)
###ZIPPING###
zipping_parser = subparsers.add_parser('zip')
zipping_parser.add_argument('inputs', help='input pdfs (file1[x:y:i] ...: uses only every ith page from x to y for file1)', nargs='+', type=CropFiles)
zipping_parser.add_argument('-r', '--ratios', help='ratio per file', nargs='*', default=0, type=int)
zipping_parser.add_argument('-o', '--output', help='output pdf', default='zip.pdf')
zipping_parser.add_argument('-i', '--inputPrefix', help='adds prefix to all input pdf names', default='')
zipping_parser.add_argument('-fn', '--formaterPlaceholderLength', help='display maximum numbers up to 10^fn properly', default=0, type=int)
zipping_parser.set_defaults(func=zipping)
###METADATA###
meta_parser = subparsers.add_parser('meta') #! not really impl yet
meta_parser.add_argument('inputs', help='input pdfs (file1[x:y:i] ...: uses only every ith page from x to y for file1)', nargs='+', type=CropFiles)
meta_parser.add_argument('-k', '--keywords', help='keywords in metadata dictionary', nargs='+')
meta_parser.add_argument('-v', '--values', help='values corresponding to keywords', nargs='+')
meta_parser.add_argument('-fn', '--formaterPlaceholderLength', help='display maximum numbers up to 10^fn properly', default=0, type=int)
###INFO###
info_parser = subparsers.add_parser('info')
info_parser.add_argument('input', help='input pdf')
info_parser.set_defaults(func=info)
###SUPERFEATURES###
super_parser = subparsers.add_parser('superfeatures')
def features(*args):
    print('''These (hidden) features can be used like everywhere:
    slicing -- if you only want to input part of a pdf, put a python slice (but only positive numbers) after the file, like this "shakepeare.pdf[400:600:5]", which means: for only every fifth page of shakespeare.pdf from page 400 to 600.

    Note that counting beginns from 0!

    multiplying -- if you have multiple input file, whose names are different only in a number, use {} to "multiply" the input. For example, "split_{0:3}" equals "split_0 split_1 split_2".
    You can even specify if the number should be preceeded with zeroes.

    Want to put a blank page in front of a pdf? Use createBlank, which uses the format of the input pdf.
    !!This feature isn't implemented yet, use blank + delete instead!!
    ''')
super_parser.set_defaults(func=features)
args = parser.parse_args()
if 'func' not in args: # for non-commandline users
    argparse.ArgumentParser.exit_after_cmd = False
    while 1:
        inp = input('stuPDF: ').split()
        if not inp:
            break
        args = parser.parse_args(inp)
        if not normal_behaviour or '-h' in inp or '--help' in inp:
            normal_behaviour = True
        else:
            args.func(args)
else:
    args.func(args)
