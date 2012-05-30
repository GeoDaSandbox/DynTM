""" This script turns templates files into Python Strings for easy deployment """
FILES = ["client.js","service.html"]

if __name__=='__main__':
    content_strings = open("content_strings.py",'w')
    content_strings.write("content_strings = {}\n");
    for fname in FILES:
        content = open(fname).read()
        content_strings.write('content_strings["%s"] = """%s"""\n\n'%(fname,content))
    content_strings.close()
        
