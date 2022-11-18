from core import *
from threading import Thread

'''
Server with a working upload feature and back-to-back texting.
One thing to note, this implementation does not have a
graceful "exit" procedure (feel free to implement one). So to
end a run with this code, you will need to use CTRL+C for both
the server and the client.
'''
connections = [] #global list of connections so server can see all connections regardless of thread

#function to handle a download request from a client
def handle_downreq_server(conn: socket, message: dict, home_dir: str) -> None:
    #see if file is in server. if so, upload it to the client
    filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1] #get filename from message

    #upload file if it exists
    if os.path.exists(f"{home_dir}/{filename}"):
        upload(conn, f"{home_dir}/{filename}",False)
    else:
        new_message = {
        PACKET_HEADER: ":DOWNLOAD:",
        PACKET_PAYLOAD: {
            "filename": filename
        }
        }
        if new_message:
            send_msg(get_other_connection(conn), pickle.dumps(new_message))

#function if given the thread's connection, and returns the socket of the other connection
def get_other_connection(conn: socket) -> socket:
    if conn == connections[0]:
        return connections[1]
    elif conn == connections[1]:
        return connections[0]

#decides what to do with messages recieved by the server
def handle_received_message_server(conn: socket, message: dict, home_dir: str) -> None:
    """Function that takes a message and then executes the appropriate actions to
       do the proper functionality in response.

    Args:
        message (dict): The message provided by the connected device.
        home_dir (str): Directory of this client/server's data (in case of uploading).
    """
    if message is not None:
        if message[PACKET_HEADER] == ":UPLOAD:":
            receive_upload(message, home_dir)
        elif message[PACKET_HEADER] == ":DOWNLOAD:":
            handle_downreq_server(conn, message, home_dir)
        elif message[PACKET_HEADER] == ":FAIL:":
            #means a file requested for download was not found. forward this message to the other client
            new_message = {
            PACKET_HEADER: ":FAIL:",
            PACKET_PAYLOAD: message[PACKET_PAYLOAD]   
            }
            send_msg(get_other_connection(conn), pickle.dumps(new_message))
        elif message[PACKET_HEADER] == ":TEMP_UPLOAD:":
            receive_upload(message, home_dir)

            #foreward the recieved file to the other connection
            filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1]
            filename = filename.split('/')[1]
            upload(get_other_connection(conn), f"{home_dir}/{filename}",True)
        elif message[PACKET_HEADER] == ":ACK_DELETE:":
            #delete the borrowed file
            filename = message[PACKET_PAYLOAD]["filename"].split(os.sep)[-1]
            print("The borrowed file has been recieved. It will now be deleted. \n")
            os.remove(f"{home_dir}/{filename}")
        elif message[PACKET_HEADER] == ":ACK:":
            print("client successfully recieved file")
        else:
            print(f"{message[PACKET_PAYLOAD]}")


def server_receiver(conn: socket, home_dir: str) -> None:
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
            handle_received_message_server(conn, received_msg, home_dir)
        except KeyboardInterrupt:
            conn.closesocket()

#thread for handling each connection from a client
def connection(conn: socket, home_dir: str):

    #create a sender and reciever thread for the connection
    sender_thread = Thread(target=sender, args=(conn, home_dir))
    receiver_thread = Thread(target=server_receiver, args=(conn, home_dir))
    sender_thread.start()
    receiver_thread.start()
    sender_thread.join()
    receiver_thread.join()

def main(argv) -> None:
    # Initialize the server socket that a client will connect to.
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((argv.host, argv.port))

    # Wait to establish a connection with a client that tries to connect.
    server_socket.listen()
    client_sock, client_addr = server_socket.accept()
    print(f"[{ctime()}] Connected to client {client_addr}.")

    #add new socket to list of connections
    connections.append(client_sock)

    #create a thread for connection 1
    conn1 = Thread(target=connection, args=(client_sock,"server_dir"))
    conn1.start()

    # Wait to establish a connection with a client that tries to connect.
    server_socket.listen()
    client_sock2, client_addr2 = server_socket.accept()
    print(f"[{ctime()}] Connected to client {client_addr2}.")

    #add new socket to list of connections
    connections.append(client_sock2)

    #create a thread for connection 2
    conn2 = Thread(target=connection, args=(client_sock2,"server_dir"))
    conn2.start()

    #join threads
    conn1.join()
    conn2.join()


    # Initialize the threads for both sending/receiving functionalities and then
    # start the threads. The purpose of this is to allow the server to have a more
    # seamless communication with the client on the other end. Otherwise, communication
    # becomes more complicated.
    

    # Start and join the threads.
    



if __name__ == "__main__":
    main(parse_args())
