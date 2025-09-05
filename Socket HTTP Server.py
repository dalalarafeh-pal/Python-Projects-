import argparse
import sys
import os
import socket
import time
import csv

MIME_types = {
    '.csv': 'text/csv',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.zip': 'application/zip',
    '.txt': 'text/plain',
    '.html': 'text/html',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def log_to_csv(server_ip, server_port, client_ip, client_port, url, status_line, content_length):
    with open('harafehSocketOutput.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Client request served", "4-Tuple:", server_ip, server_port, client_ip, client_port, "Requested URL", url, status_line, "Bytes sent:", content_length])

def log_to_text(status_line, headers):
    with open('harafehHTTPResponses.txt', 'a') as txtfile:
        txtfile.write(status_line + "\r\n" + headers + "\r\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=True)
    parser.add_argument("-d", "--directory", type=str, required=True)
    args = parser.parse_args()

    if 0 <= args.port <= 1023:
        if args.port != 80:
            print("Well-known port number {}, entered - could cause a conflict.".format(args.port))
    elif 1024 <= args.port <= 49151:
        print("Registered port number {}, entered - could cause a conflict.".format(args.port))
    else:
        sys.stderr.write("Terminating program, port number is not allowed.\n")
        return

    if not os.path.isdir(args.directory):
        sys.stderr.write("Invalid directory path.\n")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_ip = "127.0.0.1"
        server_socket.bind((server_ip, args.port))
        server_socket.listen(1)
        sys.stdout.write("Welcome socket created: {}, {}\n".format(server_ip, args.port))

        while True:
            client_socket, client_addr = server_socket.accept()
            sys.stdout.write("Connection socket created: {}, {}\n".format(client_addr[0], client_addr[1]))

            request = client_socket.recv(1024).decode()
            try:
                method, file_name, version = request.split('\r\n')[0].split()
            except ValueError:
                client_socket.close()
                continue

            curr_time = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
            headers = ""
            bytes_transmitted = 0

            if method != 'GET':
                status_line = "HTTP/1.1 501 Not Implemented"
                response = "HTTP/1.1 501 Not Implemented\r\nDate: {}\r\n\r\n".format(curr_time)
                client_socket.sendall(response.encode())
            elif version != "HTTP/1.1":
                status_line = "HTTP/1.1 505 HTTP Version Not Supported"
                response = "HTTP/1.1 505 HTTP Version Not Supported\r\nDate: {}\r\n\r\n".format(curr_time)
                client_socket.sendall(response.encode())
            else:
                file_path = os.path.join(args.directory, file_name.lstrip('/'))
                if not os.path.isfile(file_path):
                    status_line = "HTTP/1.1 404 Not Found"
                    response = "HTTP/1.1 404 Not Found\r\nDate: {}\r\n\r\n".format(curr_time)
                    client_socket.sendall(response.encode())
                    log_to_csv(server_ip, args.port, client_addr[0], client_addr[1], file_name, status_line, 0)
                else:
                    with open(file_path, 'rb') as file:
                        content = file.read()
                    file_size = len(content)
                    last_mod = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(file_path)))
                    mime_type = MIME_types.get(os.path.splitext(file_name)[-1])
                    status_line = "HTTP/1.1 200 OK"
                    headers = "Content-Length: {}\r\nContent-Type: {}\r\nDate: {}\r\nLast-Modified: {}\r\nConnection: close\r\n".format(file_size, mime_type, curr_time, last_mod)
                    response = "{}\r\n{}\r\n".format(status_line, headers)
                    client_socket.sendall(response.encode() + content)
                    log_to_csv(server_ip, args.port, client_addr[0], client_addr[1], file_name, status_line, file_size)

            log_to_text(status_line, headers)
            client_socket.close()
            sys.stdout.write("Connection to {}, {} is now closed.\n".format(client_addr[0], client_addr[1]))

if __name__ == "__main__":
    main()

