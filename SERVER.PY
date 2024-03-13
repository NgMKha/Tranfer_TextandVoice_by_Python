import socket
import threading
import sounddevice as sd
import numpy as np
import pickle

HOST = '192.168.x.x' // X -> you can change number in IP  
AUDIO_PORT = 5000  // port you can change 
TEXT_PORT = 5001  // port you can change
BUFFER_SIZE = 1024

clients = []

def handle_audio_client(client_socket, address):
    send_audio_event = threading.Event()
    receive_audio_event = threading.Event()

    def send_audio_data():
        try:
            with sd.InputStream(channels=1, dtype='int16') as stream:
                while not send_audio_event.is_set():
                    data, overflowed = stream.read(BUFFER_SIZE)
                    client_socket.sendall(data.tobytes())
        except Exception as e:
            print(f"Client {address} disconnected audio")
            remove_client(client_socket)

    def receive_audio_data():
        try:
            with sd.OutputStream(channels=1, dtype='int16') as stream:
                while not receive_audio_event.is_set():
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    stream.write(np.frombuffer(data, dtype=np.int16))
        except Exception as e:
            print(f"Client {address} disconnected audio")
            remove_client(client_socket)

    send_audio_thread = threading.Thread(target=send_audio_data)
    receive_audio_thread = threading.Thread(target=receive_audio_data)

    send_audio_thread.start()
    receive_audio_thread.start()

    send_audio_thread.join()
    receive_audio_thread.join()

def handle_text_client(client_socket, address):
    send_text_event = threading.Event()
    receive_text_event = threading.Event()

    def send_text_message():
        try:
            while not send_text_event.is_set():
                message = input("You: ")
                if not message:
                    break
                text_message = {"type": "text", "data": message}
                client_socket.sendall(pickle.dumps(text_message))
        except Exception as e:
            print(f"Client {address} disconnected message")
            remove_client(client_socket)

    def receive_text_messages():
        try:
            while not receive_text_event.is_set():
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                message = pickle.loads(data)
                if message["type"] == "text":
                    print(f"Client {address}: {message['data']}")
                    print("You: ")
        except Exception as e:
            print(f"Client {address} disconnected message")
            remove_client(client_socket)

    send_text_thread = threading.Thread(target=send_text_message)
    receive_text_thread = threading.Thread(target=receive_text_messages)

    send_text_thread.start()
    receive_text_thread.start()

    send_text_thread.join()
    receive_text_thread.join()

def remove_client(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
        client_socket.close()

def server():
    audio_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_server_socket.bind((HOST, AUDIO_PORT))
    audio_server_socket.listen()

    text_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    text_server_socket.bind((HOST, TEXT_PORT))
    text_server_socket.listen()

    print(f"Audio Server listening on {HOST}:{AUDIO_PORT}")
    print(f"Text Server listening on {HOST}:{TEXT_PORT}")

    try:
        while True:
            audio_client_socket, audio_addr = audio_server_socket.accept()
            text_client_socket, text_addr = text_server_socket.accept()
            print("Have Client connected")
            clients.append(audio_client_socket)
            clients.append(text_client_socket)

            audio_client_handler = threading.Thread(target=handle_audio_client, args=(audio_client_socket, audio_addr))
            text_client_handler = threading.Thread(target=handle_text_client, args=(text_client_socket, text_addr))

            audio_client_handler.start()
            text_client_handler.start()

    except KeyboardInterrupt:
        print("Server shutting down...")
        for client_socket in clients:
            client_socket.close()
        audio_server_socket.close()
        text_server_socket.close()

if __name__ == "__main__":
    server()
