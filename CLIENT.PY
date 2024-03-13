import socket
import threading
import sounddevice as sd
import numpy as np
import pickle

HOST = '192.168.x.x' // X -> you can change to number in IP Address same as IP in SERVER.PY 
AUDIO_PORT = 5000  // Port you can change same as AUDIO_PORT in SERVER.PY 
TEXT_PORT = 5001   // Port you can change same as TEXT_PORT in SERVER.PY and different AUDIO_PORT

BUFFER_SIZE = 1024

def handle_audio():
    audio_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_client_socket.connect((HOST, AUDIO_PORT))

    def send_audio_data():
        with sd.InputStream(channels=1, dtype='int16') as stream:
            try:
                while True:
                    data, overflowed = stream.read(BUFFER_SIZE)
                    audio_client_socket.sendall(data.tobytes())
            except (socket.error, BrokenPipeError):
                print("Connection to audio server closed")

    def receive_audio_data():
        with sd.OutputStream(channels=1, dtype='int16') as stream:
            try:
                while True:
                    data = audio_client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    stream.write(np.frombuffer(data, dtype=np.int16))
            except (socket.error, BrokenPipeError):
                print("Connection to audio server closed")

    send_audio_thread = threading.Thread(target=send_audio_data)
    receive_audio_thread = threading.Thread(target=receive_audio_data)

    send_audio_thread.start()
    receive_audio_thread.start()

    send_audio_thread.join()
    receive_audio_thread.join()

def handle_text():
    text_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    text_client_socket.connect((HOST, TEXT_PORT))

    def send_text_message():
        try:
            while True:
                message = input("You: ")
                if not message:
                    break
                text_message = {"type": "text", "data": message}
                text_client_socket.sendall(pickle.dumps(text_message))
        except (socket.error, BrokenPipeError):
            print("Connection to text server closed")

    def receive_text_messages():
        try:
            while True:
                data = text_client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                message = pickle.loads(data)
                if message["type"] == "text":
                    print(f"\nServer: {message['data']}")
                    print("You: ")
        except (socket.error, BrokenPipeError):
            print("Connection to text server closed")

    send_text_thread = threading.Thread(target=send_text_message)
    receive_text_thread = threading.Thread(target=receive_text_messages)

    send_text_thread.start()
    receive_text_thread.start()

    send_text_thread.join()
    receive_text_thread.join()

if __name__ == "__main__":
    audio_thread = threading.Thread(target=handle_audio)
    text_thread = threading.Thread(target=handle_text)

    audio_thread.start()
    text_thread.start()

    audio_thread.join()
    text_thread.join()
