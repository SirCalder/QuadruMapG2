import serial
import time

porta = '/dev/ttyACM0'
baud = 115200

print(f"[{time.strftime('%H:%M:%S')}] A tentar abrir a porta {porta} a {baud} bps...")

try:
    # Tenta abrir a conexão serial
    ser = serial.Serial(porta, baud, timeout=2)
    print(f"[{time.strftime('%H:%M:%S')}] Porta aberta com sucesso! A aguardar dados do Arduino...\n")
    print("-" * 50)

    while True:
        if ser.in_waiting > 0:
            # Lê a linha, descodifica e remove espaços em branco (como \r\n)
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"[{time.strftime('%H:%M:%S')}] LIDO: {linha}")
        else:
            time.sleep(0.1) # Evita consumo excessivo de CPU se não houver dados

except serial.SerialException as e:
    print(f"\n[ERRO] Falha ao abrir ou ler a porta serial: {e}")
    print("Dicas de Depuração:")
    print("1. O Arduino está ligado?")
    print("2. A porta mudou para ttyUSB0 ou ttyACM1? (Verifique com: dmesg | tail)")
    print("3. O seu utilizador tem permissões de 'dialout'?")
except KeyboardInterrupt:
    print("\n[INFO] Teste interrompido pelo utilizador.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("[INFO] Porta serial fechada.")
