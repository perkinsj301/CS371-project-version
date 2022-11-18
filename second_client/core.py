import argparse
import os
import pickle

from PIL import Image
from socket import socket, AF_INET, SOCK_STREAM
from time import ctime
from utils import *

def get_file_extension(filename: str) -> str:
    return filename.split('.')[1]

def receive_upload(message: dict, home_dir: str) -> None:
    # (1) Get just the filename without the prefacing path.
    # (2) Get the PIL image object.
    # (3) Save the image to the device's directory.

    filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1] #was -1
    filename = filename.split('/')[1]
    #get file extension so file can be save appropriately
    extension = get_file_extension(filename)

    #slighly different protocol for saving file depending on what type of file it is
    if extension == 'txt':
        text = message[PACKET_PAYLOAD]["txt"]
        print("got ", filename)
        with open(f"{home_dir}/{filename}", 'w') as f:
            f.write(text)
    elif extension == 'jpeg':
        print("got ", filename)
        image = message[PACKET_PAYLOAD]["img"]
        image.save(f"{home_dir}/{filename}")
    elif extension == 'mp4':
        print("got ", filename)
        vid = message[PACKET_PAYLOAD]["vid"]
        #the 'wb' option writes to the file as binary instead of text
        with open(f"{home_dir}/{filename}", 'wb') as f:
            f.write(vid)
    elif extension == 'mp3':
        print("got ", filename)
        aud = message[PACKET_PAYLOAD]["aud"]
        #the 'wb' option writes to the file as binary instead of text
        with open(f"{home_dir}/{filename}", 'wb') as f:
            f.write(aud)






def parse_args() -> argparse.Namespace:
    """Simple function that parses command-line arguments. Currently supports args
       for hostname and port number.

    Returns:
        argparse.Namespace: Arguments for establishing client-server connection.
    """
    print("Arguments for establishing client-server connection. In core")

    args = argparse.ArgumentParser()
    args.add_argument("-p", "--port", type=int, default=8080)
    args.add_argument("-n", "--host", type=str, default="localhost")
    return args.parse_args()


def upload(conn: socket, filename: str, temporary: bool) -> None:
    """Prepares a message to be sent with an IMAGE file attached to it.

    Args:
        conn (socket): Socket to send message with image to.
        filename (str): Name of the file.
        temporary (bool): denotes whether the file should stay on the device uploaded to permanantly or temporarily. 
    """

    #determine appropriate packet header
    header = ":UPLOAD:"
    if temporary:
        header = ":TEMP_UPLOAD:"

    extension = filename.split('.')[1]
    if extension == 'jpeg':
        img = Image.open(filename)

        message = {
            PACKET_HEADER: header,
            PACKET_PAYLOAD: {
                "filename": filename,
                "img": img
            }
        }
        if message:
            send_msg(conn, pickle.dumps(message))
    elif extension == 'txt':
        txt = open(filename,"r").read()

        message = {
            PACKET_HEADER: header,
            PACKET_PAYLOAD: {
                "filename": filename,
                "txt": txt #contents of the text file as text
            }
        }
        if message:
            send_msg(conn, pickle.dumps(message))
    elif extension == 'mp4':
        #the 'rb' option opens the file as binary instead of text
        vid = open(filename,"rb").read()

        message = {
            PACKET_HEADER: header,
            PACKET_PAYLOAD: {
                "filename": filename,
                "vid": vid #contents of the video file as binary
            }
        }
        if message:
            send_msg(conn, pickle.dumps(message))
    elif extension == 'mp3':
        #the 'rb' option opens the file as binary instead of text
        aud = open(filename,"rb").read()

        message = {
            PACKET_HEADER: header,
            PACKET_PAYLOAD: {
                "filename": filename,
                "aud": aud #contents of the video file as binary
            }
        }
        if message:
            send_msg(conn, pickle.dumps(message))

    


def sender(conn: socket, home_dir: str) -> None:
    """Function that will be used in a thread to handle any outgoing messages to
       the provided socket connection.

    Args:
        conn (socket): Socket connection to send messages to.
        home_dir (str): Directory where the client/server's data will be stored.
    """
    print("Function that will be used in a thread to handle any outgoing messages to the provided socket connection. In core")

    while True:
        try:
            message = input(f"[{ctime()}] ")
            print("message: ", message)
            command = message.split()[0]
            if command == ":UPLOAD:":
                filename = message.split()[1]
                upload(conn, f"{home_dir}/{filename}",False)
            else:
                message = {
                    PACKET_HEADER: ":MESSAGE:",
                    PACKET_PAYLOAD: message
                }
                if message:
                    send_msg(conn, pickle.dumps(message))
        except KeyboardInterrupt:
            conn.closesocket()

