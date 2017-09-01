import datetime
import socket
import os
import time
import sys
import shlex

sequenceno =0
packets_send_ack = []
def decimal_to_binary(number,total_number):
	get_bin = lambda x: format(x,'b')
	value = get_bin(number)
	size = len(value)
	str1 = ''
	for i in xrange(total_number-size):
		str1= '0' + str1
	return str1 + str(value)


def rdt_send(sendersocket,file, MSS,windowSize,hostname,port,file_ptr):
	global sequenceno
	global packets_send_ack
	sequenceno = file_ptr
	dataack = '0101010101010101'
	packet_list = []
	packets_send_ack[:] = []
	f = open(file,'rb')
	f.seek(file_ptr)
	data = f.read(MSS)
	while ((len(packet_list) < int(windowSize)) and data!=''):
		checksum = addchecksum(data)
		bchecksum = decimal_to_binary(checksum,16) 
		bseqno = decimal_to_binary(sequenceno,32)
		packet = str(bseqno) + str(bchecksum) + dataack + data
		packet_list.append(packet)
		sequenceno = sequenceno + len(data)
		packets_send_ack.append(sequenceno)
		data = f.read(MSS)
	for i in packet_list:
		sendersocket.sendto(i,(hostname,port))
	packet_list =[]
	f.close()
	return sequenceno

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def addchecksum(data):
    s = 0
    for i in range(0, len(data), 2):
        w = ord(data[i]) + (ord(data[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff


def main():
	HOST = ''  
	PORT = 8282
	global sequenceno
 	global dataack
 	global windowSize
 	global packets_send_ack
 	
	try :
		sendersocket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print 'Socket created'
	except socket.error, msg :
		print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
 
	try:
		sendersocket.bind((HOST, PORT))
	except socket.error , msg:
		print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	print 'Socket bind complete'

	if len(sys.argv) != 6:
		print 'Invalid Argument: Must have 4 parameters'
		exit()
	else:
		serverHostname = sys.argv[1]
		serverPort = int(sys.argv[2])
		filename = sys.argv[3]
		windowSize = sys.argv[4]
		MSS = int(sys.argv[5])

	print serverHostname, serverPort, filename, windowSize, MSS
	file_ptr =0
	recv_list= []

	stats = os.stat(filename)
	file_size = stats.st_size
	print 'File Size: ' + str(file_size)
	prev_file_ptr = file_ptr
	new_file_ptr = file_ptr
	
	# Calculating the start and end time to calculate the delay
	print 'starting time: ' + time.strftime('%l:%M:%S:%p %Z on %b %d, %Y')
	starttime = datetime.datetime.now()
	while (int(prev_file_ptr) < int(file_size)):
	
		last_acked_packet =0
		if len(recv_list)!=0:
			if len(recv_list) == len(packets_send_ack):
				prev_file_ptr = max(recv_list)
				last_acked_packet = len(packets_send_ack)
				recv_list[:] = []
			elif len(recv_list) < len(packets_send_ack):
				recv_list.sort()
				for i in xrange(len(recv_list)):
					if int(recv_list[i]) == int(packets_send_ack[i]):
						last_acked_packet = i+1
						prev_file_ptr = recv_list[i]
						continue
					elif i>0:
						prev_file_ptr = recv_list[i-1]
						break
					else:
						prev_file_ptr = prev_file_ptr
						break
				recv_list[:] = []
				print 'Timeout, Sequence Number: ' + str(prev_file_ptr)
		elif len(recv_list) ==0:
			prev_file_ptr = prev_file_ptr
			print 'Timeout, Sequence Number: '+str(prev_file_ptr)
		new_file_ptr = rdt_send(sendersocket,filename,MSS, int(windowSize) - int(last_acked_packet),serverHostname,serverPort,prev_file_ptr)
		sendersocket.settimeout(0.6)
		while True:
			try:
				message = sendersocket.recvfrom(1024)
				data = message[0]
				convert_int = str(data[0:32])
				convert_int_list= int(convert_int,2)
				recv_list.append(int(convert_int_list))
			except socket.timeout:
				break
		
	sendersocket.close()
	stoptime = datetime.datetime.now()
	print 'stop time: ' + time.strftime('%l:%M:%S:%p %Z on %b %d, %Y')
if __name__ == '__main__':
 	main()

