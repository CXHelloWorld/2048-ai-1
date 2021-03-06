''' Help the user achieve a high score in a real game of threes by using a move searcher. '''

import ctypes
import time
import os

# Enable multithreading?
MULTITHREAD = True

ailib = ctypes.CDLL('bin/2048.so')
ailib.init_move_tables()
ailib.init_score_tables()

ailib.find_best_move.argtypes = [ctypes.c_uint64]
ailib.score_toplevel_move.argtypes = [ctypes.c_uint64, ctypes.c_int]
ailib.score_toplevel_move.restype = ctypes.c_float

def to_c_board(m):
    board = 0
    i = 0
    for row in m:
        for c in row:            
            board |= c << (4*i)
            i += 1
    return board

def print_board(m):
    for row in m:
        for c in row:
            print '%8d' % c,
        print

def _to_val(c):
    if c == 0: return 0
    return 2**c

def to_val(m):
    return [[_to_val(c) for c in row] for row in m]

def _to_score(c):
    if c <= 1:
        return 0
    return (c-1) * (2**c)

def to_score(m):
    return [[_to_score(c) for c in row] for row in m]

if MULTITHREAD:
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(4)
    def score_toplevel_move(args):
        return ailib.score_toplevel_move(*args)

    def find_best_move(m):
        board = to_c_board(m)

        print_board(to_val(m))
        print "Current approx. score:", sum(_to_score(c) for row in m for c in row)

        scores = pool.map(score_toplevel_move, [(board, move) for move in xrange(4)])
        bestmove, bestscore = max(enumerate(scores), key=lambda x:x[1])
        if bestscore == 0:
            return -1
        return bestmove
else:
    def find_best_move(m):
        board = to_c_board(m)
        return ailib.find_best_move(board)

def movename(move):
    return ['up', 'down', 'left', 'right'][move]

def rungame(args):
    from gamectrl import BrowserRemoteControl, Fast2048Control, Keyboard2048Control

    if len(args) == 1:
        port = int(args[0])
    else:
        port = 32000

    ctrl = BrowserRemoteControl(port)
    # Use Keyboard2048Control if Fast2048Control doesn't seem to be working.
    gamectrl = Fast2048Control(ctrl)
    # gamectrl = Keyboard2048Control(ctrl)

    moveno = 0
    start = time.time()
    while 1:
        state = gamectrl.get_status()
        if state == 'ended':
            print "Game over."
            break
        elif state == 'won':
            time.sleep(3)
            gamectrl.continue_game()

        moveno += 1
        board = gamectrl.get_board()
        move = find_best_move(board)
        if move < 0:
            break
        print "%010.6f: Move %d: %s" % (time.time() - start, moveno, movename(move))
        gamectrl.execute_move(move)

if __name__ == '__main__':
    import sys
    rungame(sys.argv[1:])
