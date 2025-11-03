"""
ARCHIVE: diag_check.py

Development-only diagnostic. Archived in cleaned repo.
"""

if __name__ == '__main__':
    print('diag_check archived. See backup zip for original.')
import sys
files=[r'd:\Documents-D\VS Code\LTM_Nhom5_TicTacToe\server.py',
       r'd:\Documents-D\VS Code\LTM_Nhom5_TicTacToe\client.py',
       r'd:\Documents-D\VS Code\LTM_Nhom5_TicTacToe\game.py',
       r'd:\Documents-D\VS Code\LTM_Nhom5_TicTacToe\run_smoke_test.py',
       r'd:\Documents-D\VS Code\LTM_Nhom5_TicTacToe\system.json']
for f in files:
    try:
        b=open(f,'rb').read()
    except Exception as e:
        print(f, 'ERROR', e)
        continue
    print(f, 'size=', len(b), 'null_count=', b.count(b'\x00'))
    print('preview=', repr(b[:200]))
    print('-'*60)
