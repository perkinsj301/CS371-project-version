from core import *
from threading import Thread

#function to handle a download request on the client from the server
def handle_downreq_client(conn: socket, message: dict, home_dir: str) -> None:
    filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1] #get filename from message

    print("got download request")
    #upload file if it exists
    if os.path.exists(f"{home_dir}/{filename}"):
        upload(conn, f"{home_dir}/{filename}",True) #uploads the file with a packet header marking the file to only temporarily stay on server
    else:
        new_message = {
            PACKET_HEADER: ":FAIL:",
            PACKET_PAYLOAD: filename   
        }
        if message:
            send_msg(conn, pickle.dumps(new_message))

#decides what to do with recieved messages
def handle_received_message_client(conn: socket, message: dict, home_dir: str) -> None:
    """Function that takes a message and then executes the appropriate actions to
       do the proper functionality in response.

    Args:
        message (dict): The message provided by the connected device.
        home_dir (str): Directory of this client/server's data (in case of uploading).
    """
    if message is not None:
        if message[PACKET_HEADER] == ":UPLOAD:":
            receive_upload(message, home_dir)

            
            #send an acknowledgement to the server
            message = {
            PACKET_HEADER: ":ACK:",
            PACKET_PAYLOAD: ""
            }
            if message:
                send_msg(conn, pickle.dumps(message))
        elif message[PACKET_HEADER] == ":DOWNLOAD:":
            handle_downreq_client(conn, message, home_dir)

        elif message[PACKET_HEADER] == ":FAIL:":
            print("Unable to find " + message[PACKET_PAYLOAD])
        elif message[PACKET_HEADER] == ":TEMP_UPLOAD:": #doesn't make COMPLETE semantic sense, since the file will stay on client. But still needed (sends different ACK)
            receive_upload(message, home_dir)

            #make an acknowledgement to the server which will tell it its ok to delete borrowed file
            filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1]
            filename = filename.split('/')[1]
            
            message = {
            PACKET_HEADER: ":ACK_DELETE:",
            PACKET_PAYLOAD: {
                "filename": filename,
            }
            }
            if message:
                send_msg(conn, pickle.dumps(message))
        else:
            print(f"{message[PACKET_PAYLOAD]}")
    
#thread for recieving messages in the client
def client_receiver(conn: socket, home_dir: str) -> None:
    """Function that will be used in a thread to handle any incoming messages from
       the provided socket connection.

    Args:
        conn (socket): Socket connection to listen to.
        home_dir (str): Directory where the client/server's data will be stored.
    """
    while True:
        try:
            received_msg = recv_msg(conn)
            received_msg = pickle.loads(received_msg)
            handle_received_message_client(conn, received_msg, home_dir)
        except KeyboardInterrupt:
            conn.closesocket()

#function to create and send a message which will request the download of the filename passed as an argument
def download_client(conn: socket, filename: str) -> None:
    """Prepares a message to be sent with the name of the desired file.

    Args:
        conn (socket): Socket to send message with image to.
        filename (str): Name of the file.
    """
    message = {
        PACKET_HEADER: ":DOWNLOAD:",
        PACKET_PAYLOAD: {
            "filename": filename
        }
    }
    if message:
        send_msg(conn, pickle.dumps(message))

#thread for sending messages from the client
def client_sender(conn: socket, home_dir: str) -> None:
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
            elif command == ":DOWNLOAD:":
                filename = message.split()[1]
                download_client(conn, filename)
            elif command == ":DELETE:":
                filename = message.split()[1]
                os.remove(f"{home_dir}/{filename}")
            else:
                message = {
                    PACKET_HEADER: ":MESSAGE:",
                    PACKET_PAYLOAD: message
                }
                if message:
                    send_msg(conn, pickle.dumps(message))
        except KeyboardInterrupt:
            conn.closesocket()

def main(argv) -> None:
    # Connect to a server waiting for a connection. Note: the server must be activated
    # first (otherwise an error will be thrown).
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((argv.host, argv.port))
    print(f"[{ctime()}] Connected to server '{argv.host}:{argv.port}'.")

    # Initialize the threads for both sending/receiving functionalities and then
    # start the threads. The purpose of this is to allow the client to have a more
    # seamless communication with the server on the other end. Otherwise, communication
    # becomes more complicated.
    sender_thread = Thread(target=client_sender, args=(conn, "client_dir"))
    receiver_thread = Thread(target=client_receiver, args=(conn, "client_dir"))

    # Start and join the threads.
    sender_thread.start()
    receiver_thread.start()
    sender_thread.join()
    receiver_thread.join()


if __name__ == "__main__":
    main(parse_args())
