import sys, threading, ipaddress, select, os, time
from socket import *

def prompt():
	sys.stdout.write(">>> ")
	sys.stdout.flush()

class Client:
	def __init__(self, nickName, ip, port, status):
		self.nickName = nickName
		self.ip = ip
		self.port = port
		self.status = status


def listen(client, clientSkt, clientTable):
	while True:
		msg, addr = clientSkt.recvfrom(2048)

		# print ("Receive msg: " + msg.decode())

		msg = str.split(msg.decode())

		if client.status == 0:
			# broadcast: "BROADCAST tgtClientNickName tgtClientIp tgtClientPort"
			if msg[0] == "BROADCAST":
				clientTable[msg[1]] = Client(msg[1], msg[2], int(msg[3]), 1)
				prompt()
			# ONLINE_BROADCAST onlineNickName
			elif msg[0] == "ONLINE_BROADCAST":
				clientTable[msg[1]].status = 1
				prompt()

			# OFFLINE_BROADCAST offlineNickName
			elif msg[0] == "OFFLINE_BROADCAST":
				clientTable[msg[1]].status = 0
				prompt()

			else:
				continue

		else:
			# broadcast: "BROADCAST tgtClientNickName tgtClientIp tgtClientPort"
			if msg[0] == "BROADCAST":
				clientTable[msg[1]] = Client(msg[1], msg[2], int(msg[3]), 1)
				#print(msg[1], msg[2], int(msg[3]), 1)
				print("[client table updated.]")
				prompt()

			# from server: successfully update table
			elif msg[0] == "SUCC_TABLE_UPDATE":
				print("[Client table updated.]")
				prompt()

			elif msg[0] == 'GROUPCHAT_SUCCESS':
				print("[Message received by Server.]")
				prompt()

			elif msg[0] == "GROUP_CHATTING":
				#print(msg)
				senderNickName, chatMsg = msg[1], msg[2:]
				print("[Channel_Message " + senderNickName + ": " + " ".join(chatMsg) + "].")
				prompt()
				resp = "GROUPCHAT_ACK [Message received by " + msg[1] + "]"
				clientSkt.sendto(resp.encode(), addr)

			# receive a chat from other client: "send recipent msg sender"
			elif msg[0] == "send":
				senderNickName, chatMsg = msg[-1], msg[2:-1]
				print(senderNickName + ": " + " ".join(chatMsg) )
				prompt()
				# send ACK to the other client if current client is online
				msg = "CHAT_ACK [Message received by " + msg[1] + "]"
				clientSkt.sendto(msg.encode(), addr)

			# receive a CHAT_ACK from other client: "CHAT_ACK [Message received by...]"
			elif msg[0] == "CHAT_ACK":
				prompt()
				print(" ".join(msg[1:]))
				prompt()

			# receive a DEREG_SUCCESS from server when dereg request succeed
			elif msg[0] == "DEREG_SUCCESS":
				client.status = 0
				prompt()
				print(" ".join(msg[1:]))
				prompt()

			# OFFLINE_MSG fromNickName timestamp msg
			elif msg[0] == "OFFLINE_NOTIFICATION":
				print(" ".join(msg[1:]))
				prompt()

			# ONLINE_BROADCAST onlineNickName
			elif msg[0] == "ONLINE_BROADCAST":
				clientTable[msg[1]].status = 1
				print("[client table updated.]")
				prompt()

			# OFFLINE_BROADCASST offlineNickName
			elif msg[0] == "OFFLINE_BROADCAST":
				clientTable[msg[1]].status = 0
				print("[client table updated.]")
				prompt()

			elif msg[0] == "OFFLINE_ACK":
				print(" ".join(msg[1:]))
				prompt()

			elif msg[0] == "CLOSE":
				del clientTable[msg[1]]










if __name__ == "__main__":
	prompt()
	if len(sys.argv) != 6:
		print("Chat.py -c <name> <server-ip> <server-port> <client-port>")
		sys.exit(1)
	if not ipaddress.ip_address(sys.argv[3]):
		print("Not a valid ip address")
		sys.exit(1)
	nickName, serverIp, serverPort, clientPort = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
	if serverPort < 0 or serverPort > 65535 or clientPort < 0 or clientPort > 65535:
		print("[Not a valid port number]")
		sys.exit(1)

	clientSkt = socket(AF_INET, SOCK_DGRAM)
	clientTable = {}

	clientSkt.sendto(("REGIS_REQUEST " + nickName).encode(), (serverIp, serverPort))
	#print(serverIp, serverPort)

	msg, serverAddr = clientSkt.recvfrom(2048)
	msg = str.split(msg.decode())

	if msg[0]=="DUP_NAME":
		print(" ".join(msg[1:]))
		sys.exit(1)
	elif msg[0]=="REGIS_SUCCESS":
		print(" ".join(msg[1:]))
		prompt()
	else:
		pass

	client = Client(nickName, gethostbyname(gethostname()), clientPort, 1)
	threading.Thread(target=listen, args=(client, clientSkt, clientTable,)).start()

	while True:
		msg = input()
		msg = str.split(msg)
		if len(msg) == 0:
			prompt()
			continue

		if client.status == 0:
			# reg <nick-name>
			if msg[0] == 'reg':
				if len(msg) != 2:
					print("[Usage: reg <nick-name>]")
					prompt()
				elif nickName != msg[1]:
					print("[Error: wrong <nick-name>]")
					prompt()
				else:
					client.status = 1
					regMsg = " ".join(msg)
					clientSkt.sendto(regMsg.encode(), (serverIp, serverPort))
					prompt()
			else:
				prompt()
				continue

		else:
			if msg[0] == 'send':
				if len(msg)<3:
					print("[Usage: send <name> <message>]")
					prompt()
				else:
					if msg[1] not in clientTable.keys():
						print("['" + msg[1] + "' is not in your local table]")
						prompt()
					else:
						recpNickName = msg[1]
						msg1 = " ".join(msg) + " " + nickName
						#send message
						clientSkt.sendto(msg1.encode(), (clientTable[recpNickName].ip, clientTable[recpNickName].port))
						# wait for the ack
						ready = select.select([clientSkt], [], [], 0.5)
						if len(ready[0]) == 0:
							prompt()
							print("[No ACK from " + recpNickName + ", message sent to server. ]")
							prompt()
							# offline format: "OFFLINE fromNickName toNickName <time-stamp> msg "
							offlineMsg = "OFFLINE_SAVE " + nickName + " " + recpNickName + " " + " " + time.strftime(
								"%c") + " " + " ".join(msg[2:])
							clientSkt.sendto(offlineMsg.encode(), (serverIp, serverPort))

			elif msg[0] == 'dereg':
				if len(msg) !=2:
					prompt()
				else:
					deregMsg = " ".join(msg)
					times = 0
					while times < 5:
						clientSkt.sendto(deregMsg.encode(), (serverIp, serverPort))
						ready = select.select([clientSkt], [], [], 0.5)
						if len(ready[0]) == 0:
							times += 1
						else:
							break

					if times == 5:
						prompt()
						print("[Server not responding]")
						print("[Existing]")
						os.exit(1)

			elif msg[0] == 'send_all':
				if len(msg) !=2:
					prompt()
				else:
					msg1 = " ".join(msg) + " " + nickName
					times = 0
					while times < 5:
						clientSkt.sendto(msg1.encode(), (serverIp, serverPort))
						ready = select.select([clientSkt], [], [], 0.5)
						if len(ready[0]) == 0:
							times += 1
						else:
							break

					if times == 5:
						prompt()
						print("[Server not responding]")
						#os.exit(1)






			else:
				prompt()
				continue
						















