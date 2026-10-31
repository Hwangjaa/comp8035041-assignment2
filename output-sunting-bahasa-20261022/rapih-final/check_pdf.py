import fitz,sys
p=fitz.open(sys.argv[1]); text='\n'.join(x.get_text() for x in p)
print({'pages':len(p),'asterisks':text.count('*'),'reference_errors':text.count('Error: Reference source not found'),'chars':len(text)})
