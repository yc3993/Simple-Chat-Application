import sys, ipaddress, select, time
from socket import *

class Client:
    def __init__(self, nickName, ip, port, status):
        self.nickName = nickName
        self.ip = ip
        self.port = port
        self.status = status


if __name__ == "__main__":
    if len(sys.argv)!=3:
        print ("Usage: UdpChat -s <port>")
        exit(1)

    if len(sys.argv) != 3:
        print("Usage: python UdpChat.py -s <port>")
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
        #print(1)
        msg, clientAddr = serverSkt.recvfrom(2048)
        #print(1,msg.decode())
        msg = str.split(msg.decode())
        #print(msg[0])

        if msg[0] == "REGIS_REQUEST":
            if msg[1] in serverTable.keys():
                err = "DUP_NAME '" + msg[1] + "' has been registered with this server"
                serverSkt.sendto(err.encode(), clientAddr)
            else:
                #print(2)
                newClient = Client(msg[1], clientAddr[0], int(clientAddr[1]), 1)
                serverTable[msg[1]] = newClient
                serverSkt.sendto("REGIS_SUCCESS [Welcome, You are registered.]".encode(), clientAddr)

                for oldNickName, oldClient in serverTable.items():
                    if oldNickName != msg[1]:
                        # broadcast the newClient to all old clients
                        broadcast = "BROADCAST " + msg[1] + " " + newClient.ip + " " + str(newClient.port)
                        serverSkt.sendto(broadcast.encode(), (oldClient.ip, oldClient.port))

                        # broadcast every oldClient to the new client
                        broadcast = "BROADCAST " + oldNickName + " " + oldClient.ip + " " + str(oldClient.port)
                        serverSkt.sendto(broadcast.encode(), clientAddr)
        # offline format: "OFFLINE fromNickName toNickName <time-stamp> msg "
        elif msg[0] == "OFFLINE_SAVE":
            fromNickName, toNickName, timestamp, msg = msg[1], msg[2], msg[3:8], msg[8:]
            if toNickName not in offlineMsgs:
                offlineMsgs[toNickName] = []
            offlineMsgs[toNickName].append(fromNickName + ": " + " ".join(timestamp) + " " + " ".join(msg))
            serverSkt.sendto("OFFLINE_ACK [Messages received by the server and saved. ]".encode(), clientAddr)


        elif msg[0] == 'dereg':
            serverTable[msg[1]].status = 0
            # broadcast the updated table to all the online clients
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

            # after regNickName logged back, sent out all offline chat for regNickName
            if regNickName in offlineMsgs.keys():
                serverSkt.sendto("OFFLINE_NOTIFICATION You Have Messages".encode(), clientAddr)
                for offlineMsg in offlineMsgs[regNickName]:
                    serverSkt.sendto(("OFFLINE_NOTIFICATION " + offlineMsg).encode(), clientAddr)

                # after send out all offline msg for the client, clear this client's all offline message
                del offlineMsgs[regNickName]

            # broadcast the table to all the online clients
            for nickName, client in serverTable.items():
                if nickName != regNickName:
                    onlineBroadcast = "ONLINE_BROADCAST " + msg[1]
                    serverSkt.sendto(onlineBroadcast.encode(), (client.ip, client.port))


        elif msg[0] == 'send_all':
            senderNickName, chatMsg = msg[-1], msg[1:-1]
            #print(senderNickName, chatMsg)
            serverSkt.sendto("GROUPCHAT_SUCCESS [Message received by Server]".encode(), clientAddr)

            for nickName, client in serverTable.items():
                if nickName != senderNickName:
                    #print(nickName)
                    groupChat = "GROUP_CHATTING" + " " + senderNickName + " " + " ".join(chatMsg)
                    print(groupChat)

                    serverSkt.sendto(groupChat.encode(), (serverTable[nickName].ip, serverTable[nickName].port))
                    # wait for the ack
                    ready = select.select([serverSkt], [], [], 0.5)
                    if len(ready[0]) == 0:
                        if nickName not in offlineMsgs:
                            offlineMsgs[nickName] = []
                        offlineMsgs[nickName].append(senderNickName + ": " + time.strftime("%c") + " " + " ".join(chatMsg))













            # CLOSE <nick-name>
        elif msg[0] == 'CLOSE':
            del serverTable[msg[1]]

            # broadcast the all clients to delete this user from their local table
            for nickName, client in serverTable.items():
                serverSkt.sendto(("CLOSE " + msg[1]).encode(), (client.ip, client.port))





