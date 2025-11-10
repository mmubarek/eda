import serial
import serial.tools.list_ports
import time
import os
import struct

BAUD = 115200
PACKET_SIZE = 4
HANDSHAKE_TIMEOUT = 15.0 # seconds
NO_DATA_TIMEOUT = 10.0

def select_com_port():
    """List available COM ports and let the user select one."""
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No serial ports detected. Please connect a device and try again.")
        return None

    print("Available COM Ports:")
    for i, port in enumerate(ports):
        print(f"{i + 1}: {port.device} ({port.description})")

    while True:
        try:
            choice = int(input("\nSelect port number: ")) - 1
            if 0 <= choice < len(ports):
                selected_port = ports[choice].device
                print(f"\nSelected: {selected_port}\n")
                return selected_port
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def wait_for_handshake(ser, expected_value, buffer):
    """Waits for a specific 4-byte little-endian integer from the serial port."""
    print(f"--- Waiting for handshake code: 0x{expected_value:08X} ---")
    expected_bytes = struct.pack('<I', expected_value)
    start_time = time.time()
    
    while time.time() - start_time < HANDSHAKE_TIMEOUT:
        if ser.in_waiting > 0:
            buffer += ser.read(ser.in_waiting)

        if expected_bytes in buffer:
            print(f"SUCCESS: Found handshake 0x{expected_value:08X} in buffer: {buffer.hex()}")
            idx = buffer.find(expected_bytes)
            # Cut the buffer to after the handshake
            del buffer[:idx + PACKET_SIZE]
            return True
        
        time.sleep(0.05)

    print(f"\n--- TIMEOUT: Did not receive handshake 0x{expected_value:08X} after {HANDSHAKE_TIMEOUT} seconds. ---")
    print(f"Final buffer content: {buffer.hex()}")
    return False

def main():
    print("\n--- LEGv8 Program Loader & Monitor (Robust Handshake) ---\n")

    port = select_com_port()
    if not port:
        return

    while True:
        filepath = input("Enter the path to the binary program file (e.g., program.bin): ")
        if os.path.exists(filepath):
            break
        else:
            print(f"Error: File not found at '{filepath}'. Please try again.")

    try:
        with open(filepath, 'rb') as f:
            program_bytes = f.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        return

    num_bytes = len(program_bytes)
    print(f"Read {num_bytes} bytes from '{filepath}'.")

    try:
        with serial.Serial(port, BAUD, timeout=0.05) as ser:
            buffer = bytearray()
            
            # --- STAGE 1: RESET --- #
            input("\n>>> Press the RESET button on the FPGA now, then press Enter here. <<<")
            if not wait_for_handshake(ser, 1, buffer):
                print("FPGA did not acknowledge reset. Exiting.")
                return

            # --- STAGE 2: LOAD MODE --- #
            input("\n>>> Now press the START button once to enter LOAD MODE, then press Enter here. <<<")
            if not wait_for_handshake(ser, 2, buffer):
                print("FPGA did not acknowledge LOAD mode. Exiting.")
                return

            # --- STAGE 3: WRITING PROGRAM --- #
            print(f"\nSending {num_bytes} bytes to {port}...")
            ser.flushInput()
            bytes_sent = 0
            for byte in program_bytes:
                ser.write(bytes([byte]))
                bytes_sent += 1
                # A small delay can help prevent overwhelming the FPGA's UART buffer
                time.sleep(0.001)
            print(f"\rSent {bytes_sent}/{num_bytes} bytes.")
            print("\nProgram loading complete.")

            # --- STAGE 4: RUN MODE --- #
            input("\n>>> Press the START button a second time to RUN the program, then press Enter here. <<<")
            if not wait_for_handshake(ser, 3, buffer):
                print("FPGA did not acknowledge RUN mode. Exiting.")
                return
            
            # --- STAGE 5: MONITORING --- #
            print("\n--- Waiting for ALU results ---")
            last_rx_time = time.time()
            while True:
                if ser.in_waiting > 0:
                    buffer += ser.read(ser.in_waiting)
                    last_rx_time = time.time()

                while len(buffer) >= PACKET_SIZE:
                    result_bytes = buffer[:PACKET_SIZE]
                    del buffer[:PACKET_SIZE]
                    result = struct.unpack('<I', result_bytes)[0]
                    print(f"ALU Result = 0x{result:08X}")
                
                if time.time() - last_rx_time > NO_DATA_TIMEOUT:
                    print(f"\n--- No data received for {NO_DATA_TIMEOUT} seconds. Exiting. ---")
                    break
                
                time.sleep(0.01)

    except serial.SerialException as e:
        print(f"\nError: {e}")
    except KeyboardInterrupt:
        print("\nExiting program.")

if __name__ == "__main__":
    main()