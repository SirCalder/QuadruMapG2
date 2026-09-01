import serial
import time

# Usando a porta e velocidade que confirmamos
PORTA = '/dev/ttyACM0'
BAUD = 115200

print(f"A tentar ligar a {PORTA} a {BAUD} baud...")

try:
    ser = serial.Serial(PORTA, BAUD, timeout=1)
    print("Ligação bem-sucedida! A ouvir o Arduino...\n")
    
    while True:
        if ser.in_waiting > 0:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Recebido: {linha}")

except serial.SerialException as e:
    print(f"\nERRO: Não foi possível abrir a porta. Detalhes: {e}")
except KeyboardInterrupt:
    print("\nLeitura terminada pelo utilizador.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()







