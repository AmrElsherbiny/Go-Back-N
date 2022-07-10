from socket import *
from os import path
from math import ceil
from collections import deque
from threading import Thread
from random import randint
import sys
sendersocket = socket(AF_INET, SOCK_DGRAM)
print("Started Sender UDP File Transfer!")
sendersocket.bind((gethostbyname(gethostname()),0))
print(f"Your host ip and port is {sendersocket.getsockname()}")
win_size = 4
max_seg_size = 1024
timeout_val = 0.05
file = [None] * 65536
recv_queue = deque()
sendersocket.settimeout(timeout_val)
def Receiver(nextid):
    while file[nextid] is not None:
        try: 
            recv_queue.append(sendersocket.recvfrom(4))
        except timeout:
            t2 = Thread(target=Retransmitter, args=[nextid])
            t2.start()
        except: pass
def Retransmitter(nextid):
    if file[nextid] is not None:
        f_arr = file[nextid]
        if f_arr['retries'] == 10: 
            f_arr['file'].close() # if no ack received after 10 retransmissions, sender finishes and closes file 
            print(f"File transmission (ID {nextid}) has stopped (Number of retransmissions: {f_arr['num_retrans']})")
            file[nextid] = None
        else:
            f_arr['retries'] += 1
            for i in range(len(f_arr['window'])):
                sendersocket.sendto(f_arr['window'][i], f_arr['address'])
            f_arr['num_retrans'] += 1
if len(sys.argv) == 4:
    address = (sys.argv[2],int(sys.argv[3]))
    filename = sys.argv[1]
else:
    txt = input().split(" ")
    while len(txt) != 3: 
        txt = input().split(" ")
    txt.reverse()
    filename = txt.pop()
    address = (txt.pop(), int(txt.pop()))
while True:
    if path.exists(filename):
        nextid = randint(0,65535) # select an arbitrary random number
        while (file[nextid] is not None):
            nextid = randint(0,65535)
        file[nextid] = {}
        f_arr = file[nextid]
        f_arr['address'] = address
        f_arr['file'] = open(filename, "rb")
        #f_arr['file_size'] = path.getsize(filename)
        f_arr['num_chunks'] = ceil(path.getsize(filename)/(max_seg_size-8))
        f_arr['window'] = deque()
        f_arr['chunks_read'] = 0
        f_arr['base'] = 0
        f_arr['num_retrans'] = 0
        f_arr['retries'] = 0
        segment = b'\x00\x00'+(nextid).to_bytes(2, 'big')
        segment += filename.encode()+b'\x00\x00\x00\x00'
        f_arr['window'].append(segment)
        for i in [i+1 for i in range(min(f_arr['num_chunks'],win_size-1))]:
            segment = (i).to_bytes(2,'big')
            segment += (nextid).to_bytes(2, 'big')
            segment += f_arr['file'].read(max_seg_size-8)
            f_arr['chunks_read'] += 1
            if f_arr['chunks_read'] == f_arr['num_chunks']:
                endbit = b'\x00\x00\x00\x00'
            else:
                endbit = b'\x00\x00\x00\x00'
            segment += endbit
            f_arr['window'].append(segment)
        for i in range(len(f_arr['window'])):
            sendersocket.sendto(f_arr['window'][i], address)
        print(f"Started transmitting file \"{filename}\" (ID {nextid}) to address {address}")
        t1 = Thread(target=Receiver, args=[nextid])
        t1.start()
        while file[nextid] is not None:
            if len(recv_queue)<1: continue
            nextpack = recv_queue.popleft()
            if nextid != int.from_bytes(nextpack[0][2:4],'big'): continue
            if f_arr['address']!=nextpack[1]: continue
            ack_num = int.from_bytes(nextpack[0][:2],'big')  
            if ack_num not in [(i+f_arr['base'])%65536 for i in range(len(f_arr['window']))]: continue
            print(f"Received acknowledgement (ACK ID {ack_num}) (File ID {nextid})") 
            if f_arr['chunks_read'] == f_arr['num_chunks'] and f_arr['num_chunks']%65536 == ack_num:
                f_arr['num_chunks'] += f_arr['num_chunks']
                f_arr['file'].seek(0,0)
                f_arr['base'] = ack_num-win_size+1
            min1 = (ack_num-f_arr['base'])%65536+1
            min2 = f_arr['num_chunks']-f_arr['chunks_read']
            for i in [(i+f_arr['base']+win_size)%65536 for i in range(min(min1,min2))]:
                segment = (i).to_bytes(2,'big')
                segment += (nextid).to_bytes(2, 'big')
                segment += f_arr['file'].read(max_seg_size-8)
                f_arr['chunks_read'] += 1
                if f_arr['num_chunks'] == f_arr['chunks_read']:
                    endbit = b'\x00\x00\x00\x00'
                else:
                    endbit = b'\x00\x00\x00\x00'
                segment += endbit
                f_arr['window'].popleft()
                f_arr['window'].append(segment)
                f_arr['retries'] = 0
                sendersocket.sendto(f_arr['window'][-1], address)
            f_arr['base'] = (ack_num+1)%65536
    else: print("Error: cannot open and read file (file not found)")
    txt = input().split(" ")
    while len(txt) != 3: 
        txt = input().split(" ")
    txt.reverse()
    filename = txt.pop()
    address = (txt.pop(), int(txt.pop()))