"""
ARCHIVE: search_nonascii.py

Helper archived. See backup zip for the original scanner.
"""

if __name__ == '__main__':
    print('search_nonascii archived')
import os
root='.'
count=0
for dirpath,dirs,files in os.walk(root):
    for fn in files:
        if not fn.endswith(('.py','.md','.json','.txt')): continue
        path=os.path.join(dirpath,fn)
        try:
            with open(path,'r',encoding='utf-8') as f:
                for i,line in enumerate(f,1):
                    if any(ord(ch)>127 for ch in line):
                        print(path.replace('./',''), f'line {i}:', line.strip())
                        count+=1
        except Exception as e:
            print('ERROR reading',path,e)
print('Found',count,'lines with non-ASCII characters')
