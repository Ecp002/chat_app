import socket

HOST = "127.0.0.1"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server is running and waiting for messages...", flush=True)

client, addr = server.accept()
print("Client connected from", addr)

while True:
    message = client.recv(1024).decode()
    if not message:
        break
    print("Client says:", message)

    reply = input("Reply to client: ")
    client.send(reply.encode())
