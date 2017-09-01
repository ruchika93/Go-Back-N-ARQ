import socket
import sys
import os
import time
import random

next_seq = 0

def write_to_file(filename,packet_list):
	f = open(filename,'wb')
	for i in packet_list:
		f.write(str(i))
	f.close()

def decimal_to_binary(number,total_number):
	get_bin = lambda x: format(x,'b')
	value = get_bin(number)
	size = len(value)
	str1 = ''
	for i in xrange(total_number-size):
		str1= '0' + str1
	return str1 + str(value)

def carry_around_add(a, b):
	c = a + b
	return (c & 0xffff) + (c >> 16)

def checksum(data):
	s = 0
	for i in range(0, len(data), 2):
		w = ord(data[i]) + (ord(data[i+1]) << 8)
		s = carry_around_add(s, w)
	return ~s & 0xffff

def verify_checksum(message,senderchecksum):
	calculatechecksum = checksum(message)
	bcalculatechecksum = decimal_to_binary(calculatechecksum,16)
	if(bcalculatechecksum == senderchecksum):
		#print 'Checksum verified: Correct Data'
		return 1
	else:
		#print 'Invalid Checksum: Dropping the packet'
		return 0

def ack_send(serversocket,sequenceno,destaddress):
	zero = '0000000000000000'
	ackpkt = '1010101010101010'
	msg = str(sequenceno) + zero + ackpkt
	#print msg
	serversocket.sendto(msg,destaddress)

def main():
	global next_seq
	port = 7765
	sequenceno = 0
	hostname = socket.gethostname()
	#print hostname
	if len(sys.argv) != 4:
		print 'Invalid Argument: Must have 4 parameters'
		exit()
	else:
		serverPort = int(sys.argv[1])
		filename = sys.argv[2]
		probability = float(sys.argv[3])
	if os.path.exists(filename):
		os.remove(filename)
	#print serverPort, filename, probability
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	serversocket.bind(("", port))
	packet_list = []
	while True:
		data,addr = serversocket.recvfrom(1500)
		loss_prob = random.random()
		sequenceno = data[0:32]
		senderchecksum = data[32:48]
		senderack = data[49:63]
		message = data[64:]
		convert_int = str(sequenceno)
		convert_int_seq = int(convert_int,2)
		if float(loss_prob) <= float(probability):
			print 'Packet Loss, Sequence Number:(p)' + str(convert_int_seq)
			next_seq = next_seq
			continue
	#	print 'Packet_seq_no: ' + str(convert_int_seq)
	#	print 'Needed seq_no: ' + str(next_seq)
		if int(convert_int_seq) == int(next_seq):
			#packet_list.append(message)
			#next_seq = next_seq + len(message)
			if verify_checksum(message,senderchecksum):
				packet_list.append(message)
				ack_number = convert_int_seq +len(message)
				b_ack = decimal_to_binary(ack_number,32)
				ack_send(serversocket,b_ack,addr)
				write_to_file(filename,packet_list)
				next_seq = next_seq + len(message)
				continue
			else:
				next_seq = next_seq
				print 'Packet Loss, Sequence Number:(c)' + str(convert_int_seq)
				continue
		#else:
		#	next_seq = next_seq
		#	print 'Packet Loss, Sequence Number:(o)' + str(convert_int_seq)
		#	continue

		elif int(convert_int_seq) < int(next_seq):
                        #packet_list.append(message)
                        next_seq = next_seq
                        #if verify_checksum(message,senderchecksum):
                        ack_number = convert_int_seq +len(message)
                        b_ack = decimal_to_binary(ack_number,32)
                        ack_send(serversocket,b_ack,addr)
                        #        write_to_file(filename,packet_list)
                        continue
                        #else:
                         #       next_seq = convert_int_seq
                          #      print 'Packet Loss, Sequence Number:(c)' + str(convert_int_seq)
                           #     continue
                else:
                        next_seq = next_seq
                        print 'Packet Loss, Sequence Number:(o)' + str(convert_int_seq)
                        continue

if __name__ == '__main__':
	main()
