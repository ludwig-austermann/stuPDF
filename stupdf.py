# Ludwig Austermann
# stuPDF
# visit www.github.com/ludwig-austermann to view the project

#personal fave: stupdf blanks <input file> -sep 1 -s <end index> -e <biblio> -t 160 -cwb
# PyInstaller stupdf.py -F -n stuPDF
import PyPDF2, argparse, random


def calc_blanks(in_pages, out_pages):
    return out_pages // (out_pages - in_pages)


def save(pdf, args):
    with open(args.output + args.autoAddPdf, "wb") as file: #saving
        pdf.write(file)

    print(f"Done, pdf saved as '{args.output}{args.autoAddPdf}'.")


def blanks(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))
    write_pdf = PyPDF2.PdfFileWriter()
    sty_pdf = PyPDF2.PdfFileReader(open(args.blankPageStyle + args.autoAddPdf, "rb")) if args.blankPageStyle else None

    sep = args.seperate if args.seperate else calc_blanks(read_pdf.numPages - args.start, args.total - args.start)
    num = args.blanksnum if not args.allowMoreBlanks else (args.total - read_pdf.numPages) // (read_pdf.numPages - args.start)

    for i, page in enumerate(read_pdf.pages):
        write_pdf.addPage(page)

        if args.end and i >= args.end + args.countFromOne: #after usersetted end
            continue

        if args.nonregular: #if user wants to recalculate sep
            sep = calc_blanks(read_pdf.numPages - i, args.total - i)

        if i >= args.start + args.countFromOne and sep and not (i + args.start + args.countFromOne) % sep: #insertion of blankpages
            for _ in range(num):
                if sty_pdf:
                    write_pdf.addPage(sty_pdf.getPage(args.blankPageStylePageNum))
                else:
                    write_pdf.addBlankPage()

    if args.total < write_pdf.getNumPages(): #warning message if too many pages
        print(f"Warning, more pages ({write_pdf.getNumPages()}) than total ({args.total}).")

    if args.completeWithBlanks: #completition to total
        for _ in range(args.total - write_pdf.getNumPages()):
            if sty_pdf:
                write_pdf.addPage(sty_pdf.getPage(args.blankPageStylePageNum))
            else:
                write_pdf.addBlankPage()

    save(write_pdf, args)


def insert(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))
    write_pdf = PyPDF2.PdfFileWriter()
    if args.insertfile != "_":
        pa = PyPDF2.PdfFileReader(open(args.insertfile + args.autoAddPdf, "rb"))

    for i, page in enumerate(read_pdf.pages):
        if i - args.countFromOne in args.pages:
            if args.insertfile == "_":
                write_pdf.addBlankPage()
            else:
                write_pdf.addPage(pa)
        else:
            write_pdf.addPage(page)

    save(write_pdf, args)


def splitter(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))
    write_pdfs = [PyPDF2.PdfFileWriter()]

    for i, page in enumerate(read_pdf.pages):
        if i - args.countFromOne in args.splitPages:
            write_pdfs.append(PyPDF2.PdfFileWriter())
        write_pdfs[-1].addPage(page)

    for i, wpdf in enumerate(write_pdfs):
        with open(f"{args.outputPrefix}{i}.pdf", "wb") as file: #saving
            wpdf.write(file)

    print(f"Done, saved files {args.outputPrefix}1.pdf to {args.outputPrefix}{len(write_pdfs) - 1}.pdf.")


def merger(args):
    merger_pdf = PyPDF2.PdfFileMerger()

    for pdf in args.inputs:
        merger_pdf.append(open(args.inputPrefix + pdf + args.autoAddPdf, "rb"))

    save(merger_pdf, args)


def rotate(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))
    write_pdf = PyPDF2.PdfFileWriter()

    for i, page in enumerate(read_pdf.pages):
        if args.pages and i in args.pages:
            write_pdf.addPage(page)
        else:
            write_pdf.addPage(page.rotateCounterClockwise(args.angle))

    save(write_pdf, args)


def cute(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))
    write_pdf = PyPDF2.PdfFileWriter()

    for i in range(0, read_pdf.numPages, 2):
        read_pdf.getPage(i).rotateCounterClockwise(90).scaleBy(0.5)
        read_pdf.getPage(i + 1).rotateCounterClockwise(90).scaleBy(0.5)
        read_pdf.getPage(i).mergePage(read_pdf.getPage(i + 1))
        write_pdf.addPage(read_pdf.getPage(i))

    if read_pdf.numPages & 1:
        #write_pdf.addPage()
        pass

    save(write_pdf, args)


def delete(args):
    read_pdf = PyPDF2.PdfFileReader(args.input + args.autoAddPdf, "rb")
    write_pdf = PyPDF2.PdfFileWriter()

    for i, page in enumerate(read_pdf.pages):
        if i not in args.pages:
            write_pdf.addPage(page)

    save(write_pdf, args)


def overlay(args):
    read_pdf = PyPDF2.PdfFileReader(open(args.inputPrefix + args.inputs[0] + args.autoAddPdf, "rb"))
    write_pdf = PyPDF2.PdfFileWriter()
    pdfs = []

    for pdf in args.inputs[1:]:
        pdfs.appends(PyPDF2.PdfFileReader(open(args.inputPrefix + pdf + args.autoAddPdf, "rb")))

    for i, page in enumerate(read_pdf):
        for pdf in pdfs:
            if i >= pdf.numPages:
                continue
            page.mergePage(pdf.getPage(i))
        write_pdf.addPage(page)

    save(write_pdf, args)


def shuffle(args):
    shuf = list(PyPDF2.PdfFileReader(args.input + args.autoAddPdf, "rb").pages)
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
    pdfs = []

    for pdf in args.inputs:
        pdfs.append(iter(PyPDF2.PdfFileReader(open(args.inputPrefix + pdf + args.autoAddPdf, "rb")).pages))

    for page in newzip(pdfs, args.ratios):
        write_pdf.addPage(page)

    save(write_pdf, args)


def info(args):
    info_pdf = PyPDF2.PdfFileReader(open(args.input + args.autoAddPdf, "rb"))

    for i in info_pdf.documentInfo:
        print(f"{i:{20}}:\t{info_pdf.documentInfo[i]}")
    print(f"pages               :\t{info_pdf.numPages}")
    print(f"outlines            :\t{info_pdf.outlines}")
    print(f"page layout         :\t{info_pdf.pageLayout}")
    print(f"page mode           :\t{info_pdf.pageMode}")
    print(f"encrypted           :\t{info_pdf.isEncrypted}")
    print(f"xmpMetadata         :\t{info_pdf.xmpMetadata}")


parser = argparse.ArgumentParser(description="A simple solution inserting blank pages into an existing pdf but also those standard features like splitting, merging, etc.", epilog="You can easily contribute to the project. More infos on version.")
parser.add_argument("-cfo", "--countFromOne", help="enables natural counting", action="store_true")
parser.add_argument("-pdf", "--autoAddPdf", help="automatically adds .pdf to files", action="store_const", const=".pdf", default="")
parser.add_argument("-v", "--version", action="version", version="stupdf 0.3.0\nContribute to the project on github:\ngithub.com/austermann\n\nchangelog: added insert and blank function\ncode cleanup")
subparsers = parser.add_subparsers()
###BLANKS###
blanks_parser = subparsers.add_parser("blanks")
blanks_parser.add_argument("input", help="input pdf")
blanks_parser.add_argument("-o", "--output", help="output pdf", default="blanks.pdf")
blanks_parser.add_argument("-sep", "--seperate", help="insert every sep pages the blank page", type=int)
blanks_parser.add_argument("-s", "--start", help="start from page", default=0, type=int)
blanks_parser.add_argument("-e", "--end", help="end at page", type=int)
blanks_parser.add_argument("-t", "--total", help="total pages of output, if no sep, calculates sep itself", default=0, type=int)
exbla = blanks_parser.add_argument_group("extra options", "using pro features")
exbla.add_argument("-num", "--blanksnum", help="number of blank pages per sep", default=1, type=int)
exbla.add_argument("-cwb", "--completeWithBlanks", action="store_true")
exbla.add_argument("-amb", "--allowMoreBlanks", action="store_true")
exbla.add_argument("-nreg", "--nonregular", help="calculates pages every loop", action="store_true")
exbla.add_argument("-style", "--blankPageStyle", help="use first page of pdf as blankpage")
exbla.add_argument("-stynum", "--blankPageStylePageNum", help="which page in pdf (default 0)", default=0, type=int)
blanks_parser.set_defaults(func=blanks)
###BLANK###
blank_parser = subparsers.add_parser("blank")
blank_parser.add_argument("input", help="input pdf")
blank_parser.add_argument("-p", "--pages", help="pages, where to insert", nargs="+", default=0, type=int)
blank_parser.add_argument("-o", "--output", help="output pdf", default="blank.pdf")
blank_parser.set_defaults(func=insert, insertfile="_")
###INSERT###
insert_parser = subparsers.add_parser("insert")
insert_parser.add_argument("input", help="input pdf")
insert_parser.add_argument("insertfile", help="insert pdf, if '_' inserts blanks")
insert_parser.add_argument("-p", "--pages", help="pages, where to insert", nargs="+", default=0, type=int)
insert_parser.add_argument("-o", "--output", help="output pdf", default="insert.pdf")
blank_parser.set_defaults(func=insert)
###SPLIT###
split_parser = subparsers.add_parser("split")
split_parser.add_argument("input", help="input pdf")
split_parser.add_argument("splitPages", help="pages, where to split", nargs="+", type=int)
split_parser.add_argument("-o", "--outputPrefix", help="outputs prefix", default="split_")
split_parser.set_defaults(func=splitter)
###MERGE###
merge_parser = subparsers.add_parser("merge")
merge_parser.add_argument("inputs", help="input files", nargs="+")
merge_parser.add_argument("-o", "--output", help="output pdf", default="merge.pdf")
merge_parser.add_argument("-i", "--inputPrefix", help="adds prefix to all input pdf names", default="")
merge_parser.set_defaults(func=merger)
###ROTATE###
rotate_parser = subparsers.add_parser("rotate")
rotate_parser.add_argument("input", help="input pdf")
rotate_parser.add_argument("angle", help="angle to rotate the pdf (counterclockwise in degrees)", default=90, type=int)
rotate_parser.add_argument("-o", "--output", help="output pdf", default="rotate.pdf")
rotate_parser.add_argument("-p", "--pages", help="only selected pages", nargs="*", type=int)
rotate_parser.set_defaults(func=rotate)
###CUTE###
cute_parser = subparsers.add_parser("cute", description="Transform a pdf to one with two pages per page.")
cute_parser.add_argument("input", help="input pdf")
cute_parser.add_argument("-o", "--output", help="output pdf", default="cute.pdf")
cute_parser.set_defaults(func=cute)
###DELETE###
delete_parser = subparsers.add_parser("delete")
delete_parser.add_argument("input", help="input pdf")
delete_parser.add_argument("pages", help="pages to delete", nargs="+", type=int)
delete_parser.add_argument("-o", "--output", help="output pdf", default="delete.pdf")
delete_parser.set_defaults(func=delete)
###OVERLAY###
overlay_parser = subparsers.add_parser("overlay")
overlay_parser.add_argument("inputs", help="input pdfs", nargs="+")
overlay_parser.add_argument("-o", "--output", help="output pdf", default="overlay.pdf")
overlay_parser.set_defaults(func=overlay)
###SHUFFLE###
shuffle_parser = subparsers.add_parser("shuffle")
shuffle_parser.add_argument("input", help="input pdf")
shuffle_parser.add_argument("-o", "--output", help="output pdf", default="shuffle.pdf")
shuffle_parser.set_defaults(func=shuffle)
###ZIPPING###
zipping_parser = subparsers.add_parser("zip")
zipping_parser.add_argument("inputs", help="input pdfs", nargs="+")
zipping_parser.add_argument("-r", "--ratios", help="ratio per file", nargs="*", default=0, type=int)
zipping_parser.add_argument("-o", "--output", help="output pdf", default="zip.pdf")
zipping_parser.add_argument("-i", "--inputPrefix", help="adds prefix to all input pdf names", default="")
zipping_parser.set_defaults(func=zipping)
###METADATA###
meta_parser = subparsers.add_parser("meta")
meta_parser.add_argument("inputs", help="input pdfs", nargs="+")
meta_parser.add_argument("-k", "--keywords", help="keywords in metadata dictionary", nargs="+")
meta_parser.add_argument("-v", "--values", help="values corresponding to keywords", nargs="+")
###INFO###
info_parser = subparsers.add_parser("info")
info_parser.add_argument("input", help="input pdf")
info_parser.set_defaults(func=info)
args = parser.parse_args()
args.func(args)
