import socket
import sys

def send_command(ip, port, func, parameters, device_id, password):
    pkt = bytearray()
    pkt.extend(b'\xFD\xFD')  # Start
    pkt.append(0x02)         # Protokolltyp

    # Device-ID
    device_id_bytes = device_id.encode("ascii")
    pkt.append(len(device_id_bytes))
    pkt.extend(device_id_bytes)

    # Passwort
    password_bytes = password.encode("ascii")
    pkt.append(len(password_bytes))
    pkt.extend(password_bytes)

    # Funktion
    pkt.append(func)

    # Parameter
    for param_id, value in parameters.items():
        pkt.append(param_id & 0xFF)
        pkt.append(value & 0xFF)

    # Checksumme
    chksum = sum(pkt[2:]) & 0xFFFF
    pkt.append(chksum & 0xFF)
    pkt.append((chksum >> 8) & 0xFF)

    # Formatiere das gesendete Paket: Zweiergruppen mit Leerzeichen
    raw_pkt = " ".join(f"{b:02x}" for b in pkt)
    print("{:<25} {}".format("Sending UDP packet:", raw_pkt))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3.0)
    sock.sendto(bytes(pkt), (ip, port))

    try:
        response, _ = sock.recvfrom(256)
        raw_response = " ".join(f"{b:02x}" for b in response)
        print("{:<25} {}".format("Received UDP packet:", raw_response))
    except socket.timeout:
        print("Timeout: Keine Antwort erhalten.")

if __name__ == "__main__":
    usage = ("Usage: python udp_test.py <IP> <device_id> <password> "
             "[<speed: 33|66|99>] [<oscillation: on|off>]")
    if len(sys.argv) < 4:
        print(usage)
        sys.exit(1)
    IP = sys.argv[1]
    device_id = sys.argv[2]
    password = sys.argv[3]
    PORT = 4000  # Standard-Port, ggf. anpassen

    # Standard: Lüfter einschalten
    parameters = {0x01: 1}

    # Optional: Lüftergeschwindigkeit
    if len(sys.argv) >= 5:
        try:
            speed_input = int(sys.argv[4])
        except ValueError:
            print("Speed must be a number (33, 66 or 99).")
            sys.exit(1)
        if speed_input == 33:
            speed_cmd = 1
        elif speed_input == 66:
            speed_cmd = 2
        elif speed_input == 99:
            speed_cmd = 3
        else:
            print("Invalid speed value. Must be 33, 66 or 99.")
            sys.exit(1)
        parameters[0x02] = speed_cmd  # Übergebe den diskreten Wert (1, 2 oder 3)

    # Optional: Oszillation
    if len(sys.argv) >= 6:
        osc_input = sys.argv[5].lower()
        if osc_input == "on":
            osc_value = 1
        elif osc_input == "off":
            osc_value = 0
        else:
            print("Invalid oscillation value. Use 'on' or 'off'.")
            sys.exit(1)
        parameters[0xB7] = osc_value

    send_command(IP, PORT, 0x03, parameters, device_id, password)
