import sys, threading, ipaddress, select, os, time
from socket import *



class Client:
	def __init__(self, nickName, ip, port, status):
		self.nickName = nickName
		self.ip = ip
		self.port = port
		self.status = status

def prompt():
	sys.stdout.write(">>> ")
	sys.stdout.flush()


def listen(client, clientSkt, clientTable):
	while True:
		msg, addr = clientSkt.recvfrom(2048)

		# print ("Receive msg: " + msg.decode())

		msg = str.split(msg.decode())

		if client.status == 0:

			if msg[0] == "BROADCAST":
				clientTable[msg[1]] = Client(msg[1], msg[2], int(msg[3]), 1)
				prompt()

			elif msg[0] == "ONLINE_BROADCAST":
				clientTable[msg[1]].status = 1
				prompt()


			elif msg[0] == "OFFLINE_BROADCAST":
				clientTable[msg[1]].status = 0
				prompt()

			else:
				continue

		else:

			if msg[0] == "BROADCAST":
				clientTable[msg[1]] = Client(msg[1], msg[2], int(msg[3]), 1)
				#print(msg[1], msg[2], int(msg[3]), 1)
				print("[client table updated.]")
				prompt()


			elif msg[0] == "SUCC_TABLE_UPDATE":
                #print(msg
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


			elif msg[0] == "send":
				senderNickName, chatMsg = msg[-1], msg[2:-1]
				print(senderNickName + ": " + " ".join(chatMsg) )
				prompt()

				msg = "CHAT_ACK [Message received by " + msg[1] + "]"
				clientSkt.sendto(msg.encode(), addr)


			elif msg[0] == "CHAT_ACK":
				prompt()
				print(" ".join(msg[1:]))
				prompt()


			elif msg[0] == "DEREG_SUCCESS":
				client.status = 0
				prompt()
				print(" ".join(msg[1:]))
				prompt()

			elif msg[0] == "OFFLINE_NOTIFICATION":
				print(" ".join(msg[1:]))
				prompt()


			elif msg[0] == "ONLINE_BROADCAST":
				clientTable[msg[1]].status = 1
				print("[client table updated.]")
				prompt()


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
    if sys.argv[1]=="-s":
        if len(sys.argv) != 3:
            print("python3 ChatApp.py -s <port>")
            exit(1)

        if len(sys.argv) != 3:
            print("python3 ChatApp.py -s <port>")
            print("python3 ChatApp.py -s <port>")
            exit(1)

        serverPort = int(sys.argv[2])
        if serverPort < 0 or serverPort > 65535:
            print("not a valid port number")
            exit(1)

        serverSkt = socket(AF_INET, SOCK_DGRAM)
        serverSkt.bind(('', serverPort))
        print("The server is ready to receive")

        serverTable, offlineMsgs = dict(), dict()

        while True:
            # print(1)
            msg, clientAddr = serverSkt.recvfrom(2048)
            # print(1,msg.decode())
            msg = str.split(msg.decode())
            # print(msg[0])

            if msg[0] == "REGIS_REQUEST":
                if msg[1] in serverTable.keys():
                    err = "DUP_NAME '" + msg[1] + "' has been registered with this server"
                    serverSkt.sendto(err.encode(), clientAddr)
                else:
                    # print(2)
                    newClient = Client(msg[1], clientAddr[0], int(clientAddr[1]), 1)
                    serverTable[msg[1]] = newClient
                    serverSkt.sendto("REGIS_SUCCESS [Welcome, You are registered.]".encode(), clientAddr)

                    for oldNickName, oldClient in serverTable.items():
                        if oldNickName != msg[1]:

                            broadcast = "BROADCAST " + msg[1] + " " + newClient.ip + " " + str(newClient.port)
                            serverSkt.sendto(broadcast.encode(), (oldClient.ip, oldClient.port))


                            broadcast = "BROADCAST " + oldNickName + " " + oldClient.ip + " " + str(oldClient.port)
                            serverSkt.sendto(broadcast.encode(), clientAddr)

            elif msg[0] == "OFFLINE_SAVE":
                fromNickName, toNickName, timestamp, msg = msg[1], msg[2], msg[3:8], msg[8:]
                if toNickName not in offlineMsgs:
                    offlineMsgs[toNickName] = []
                offlineMsgs[toNickName].append(fromNickName + ": " + " ".join(timestamp) + " " + " ".join(msg))
                serverSkt.sendto("OFFLINE_ACK [Messages received by the server and saved. ]".encode(), clientAddr)


            elif msg[0] == 'dereg':
                serverTable[msg[1]].status = 0

                for nickName, client in serverTable.items():
                    if nickName != msg[1]:
                        offlineBroadcast = "OFFLINE_BROADCAST " + msg[1]
                        serverSkt.sendto(offlineBroadcast.encode(), (client.ip, client.port))

                serverSkt.sendto("DEREG_SUCCESS [You are Offline. Bye.]".encode(), clientAddr)

            elif msg[0] == 'reg':
                regNickName = msg[1]
                if regNickName not in serverTable.keys():
                    serverTable[regNickName] = Client(regNickName, clientAddr[0], int(clientAddr[1]), 1)
                else:
                    serverTable[regNickName].ip = clientAddr[0]
                    serverTable[regNickName].port = int(clientAddr[1])
                    serverTable[regNickName].status = 1


                if regNickName in offlineMsgs.keys():
                    serverSkt.sendto("OFFLINE_NOTIFICATION You Have Messages".encode(), clientAddr)
                    for offlineMsg in offlineMsgs[regNickName]:
                        serverSkt.sendto(("OFFLINE_NOTIFICATION " + offlineMsg).encode(), clientAddr)


                    del offlineMsgs[regNickName]


                for nickName, client in serverTable.items():
                    if nickName != regNickName:
                        onlineBroadcast = "ONLINE_BROADCAST " + msg[1]
                        serverSkt.sendto(onlineBroadcast.encode(), (client.ip, client.port))


            elif msg[0] == 'send_all':
                senderNickName, chatMsg = msg[-1], msg[1:-1]
                # print(senderNickName, chatMsg)
                serverSkt.sendto("GROUPCHAT_SUCCESS [Message received by Server]".encode(), clientAddr)

                for nickName, client in serverTable.items():
                    if nickName != senderNickName:
                        # print(nickName)
                        groupChat = "GROUP_CHATTING" + " " + senderNickName + " " + " ".join(chatMsg)
                        print(groupChat)

                        serverSkt.sendto(groupChat.encode(), (serverTable[nickName].ip, serverTable[nickName].port))

                        ready = select.select([serverSkt], [], [], 0.5)
                        if len(ready[0]) == 0:
                            if nickName not in offlineMsgs:
                                offlineMsgs[nickName] = []
                            offlineMsgs[nickName].append(
                                senderNickName + ": " + time.strftime("%c") + " " + " ".join(chatMsg))


            elif msg[0] == 'CLOSE':
                del serverTable[msg[1]]


                for nickName, client in serverTable.items():
                    serverSkt.sendto(("CLOSE " + msg[1]).encode(), (client.ip, client.port))
    elif sys.argv[1]=="-c":
        if len(sys.argv) != 6:
            print("ChatApp.py -c <name> <server-ip> <server-port> <client-port>")
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
        # print(serverIp, serverPort)

        msg, serverAddr = clientSkt.recvfrom(2048)
        msg = str.split(msg.decode())

        if msg[0] == "DUP_NAME":
            print(" ".join(msg[1:]))
            sys.exit(1)
        elif msg[0] == "REGIS_SUCCESS":
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
                    if len(msg) < 3:
                        print("[Usage: send <name> <message>]")
                        prompt()
                    else:
                        if msg[1] not in clientTable.keys():
                            print("['" + msg[1] + "' is not in your local table]")
                            prompt()
                        else:
                            recpNickName = msg[1]
                            msg1 = " ".join(msg) + " " + nickName

                            clientSkt.sendto(msg1.encode(),
                                             (clientTable[recpNickName].ip, clientTable[recpNickName].port))

                            ready = select.select([clientSkt], [], [], 0.5)
                            if len(ready[0]) == 0:
                                prompt()
                                print("[No ACK from " + recpNickName + ", message sent to server. ]")
                                prompt()

                                offlineMsg = "OFFLINE_SAVE " + nickName + " " + recpNickName + " " + " " + time.strftime(
                                    "%c") + " " + " ".join(msg[2:])
                                clientSkt.sendto(offlineMsg.encode(), (serverIp, serverPort))

                elif msg[0] == 'dereg':
                    if len(msg) != 2:
                        prompt()
                    else:
                        deregMsg = " ".join(msg)
                        locker = threading.Lock()
                        locker.acquire()

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

                        locker.release()

                elif msg[0] == 'send_all':
                    if len(msg) != 2:
                        prompt()
                    else:
                        msg1 = " ".join(msg) + " " + nickName
                        locker = threading.Lock()
                        locker.acquire()
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
                        # os.exit(1)
                        locker.release()
                else:
                    prompt()
                    continue
