from socket import *
from threading import Thread
from time import time
from time import ctime
from os import path
from random import randint
import matplotlib.pyplot as plt
from collections import deque
plotque = deque()
def DrawPlot(x,y,z):
    plt.figure(figsize=(20,9))
    for i in range(len(x)):
        if z[i] == 1:
            marker='^'
            plt.scatter(x[i], y[i],  marker=marker)
        else:
            marker='o'
            plt.scatter(x[i], y[i],  marker=marker)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Packet ID")
    plt.title("Transmission Graph")
    plt.show()
clientsocket = socket(AF_INET, SOCK_DGRAM)
print("Started Receiver UDP File Transfer!")
clientsocket.bind((gethostbyname(gethostname()),0))
print(f"Your host ip and port is {clientsocket.getsockname()}")
max_seg_size = 65536 # set it to most maximum
recv_queue = deque()
#sched_timer = deque()
def Receiver():
    while True:
        try: 
            recv_queue.append(clientsocket.recvfrom(max_seg_size))
        except: pass
t1 = Thread(target=Receiver, args=[])
t1.start()
def Processor():
    file = [None] * 65536
    while True:
        if len(recv_queue)<1: continue
        nextpack = recv_queue.popleft()
        if randint(0,100)<10:
            print("Packet is received and assumed as lost!")
        else:
            fileid = int.from_bytes(nextpack[0][2:4],'big')
            packid = int.from_bytes(nextpack[0][:2],'big')
            if file[fileid] is None:
                if packid != 0: continue
                file[fileid] = {}
                f_arr = file[fileid]
                f_arr['start_time'] = time()
                f_arr['start_date'] = ctime()
                filename = nextpack[0][4:-4].decode()
                if path.exists(filename):
                    c = 2
                    splitted = filename.split(".")
                    splitted[-2] = splitted[-2] +" (2)"
                    newfilename = ".".join(splitted)
                    while path.exists(newfilename):
                        c += 1
                        splitted = filename.split(".")
                        splitted[-2] = splitted[-2] +" ("+str(c)+")"
                        newfilename = ".".join(splitted)
                    f_arr['file'] = open(newfilename, "wb")
                else: f_arr['file'] = open(filename, "wb")
                f_arr['address'] = nextpack[1]
                f_arr['total_bytes'] = len(nextpack[0])
                f_arr['total_packets'] = 1
                f_arr['last_pack'] = 0
                f_arr['ids'] = [packid]
                f_arr['type_ids'] = [0]
                print(f"First packet is received (Packet ID 0) (File ID {fileid})")
                f_arr['timestamp'] = [time()]
                clientsocket.sendto(nextpack[0][:4],nextpack[1]) # Send first acknowledgement
                continue
            f_arr = file[fileid]
            if f_arr['address'] != nextpack[1]: continue
            f_arr['total_bytes'] += len(nextpack[0])
            f_arr['total_packets'] += 1
            if packid == (f_arr['last_pack']+1)%65536:  
                f_arr['file'].write(nextpack[0][4:-4])
                f_arr['last_pack'] = packid
                f_arr['ids'].append(packid)
                f_arr['type_ids'].append(0)
                print(f"Received packet in order (Packet ID {packid}) (File ID {fileid})")
                f_arr['timestamp'].append(time())
                if nextpack[0][-4:] == b'\xff\xff\xff\xff':
                    print(f"Receiver UDP File Transfer (File ID {fileid}) has successfully finished!")
                    clientsocket.sendto(nextpack[0][:4],nextpack[1]) # reached or not, i will finish!
                    f_arr['file'].close()
                    f_arr['end_time'] = time()
                    f_arr['end_date'] = ctime()
                    print(f"Start time: {f_arr['start_date']}")
                    print(f"End time: {f_arr['end_date']}")
                    print(f"Time elapsed: {f_arr['end_time']-f_arr['start_time']:.2f} seconds")
                    if f_arr['end_time']-f_arr['start_time'] == 0: end += 0.000001
                    byte_per_sec = f_arr['total_bytes']/(f_arr['end_time']-f_arr['start_time'])
                    pack_per_sec = f_arr['total_packets']/(f_arr['end_time']-f_arr['start_time'])
                    print(f"The whole transmission took on average: {pack_per_sec:.0f} packets/sec ({byte_per_sec:.0f} bytes/sec)")
                    print(f"Total number of all received packets: {f_arr['total_packets']} packets ({f_arr['total_bytes']} bytes)")
                    f_arr['timestamp'] = [i-f_arr['start_time'] for i in f_arr['timestamp']]
                    plotque.append([f_arr['timestamp'],f_arr['ids'],f_arr['type_ids']])
                    file[fileid] = None
                    continue
            else: 
                f_arr['ids'].append(packid)
                f_arr['type_ids'].append(1)
                print(f"Received packet out of order (Packet ID {packid}) (File ID {fileid})")
                f_arr['timestamp'].append(time())
            clientsocket.sendto((f_arr['last_pack']).to_bytes(2,'big')+nextpack[0][2:4],nextpack[1])
t2 = Thread(target=Processor, args=[])
t2.start()
while True:
    if len(plotque)<1: continue
    nextplot = plotque.popleft()
    DrawPlot(nextplot[0],nextplot[1],nextplot[2])