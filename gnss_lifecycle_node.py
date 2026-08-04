#!/usr/bin/env python3
import rclpy
from rclpy.lifecycle import Node, Publisher, State, TransitionCallbackReturn
from sensor_msgs.msg import NavSatFix
import serial

class GNSSLifecycleNode(Node):
    def __init__(self):
        # Inicializa o nó com o nome 'gnss_edge_node'
        super().__init__('gnss_edge_node')
        
        # Parâmetros padrão
        self.serial_port = '/dev/ttyUSB0'
        self.baudrate = 115200
        self.ser = None
        self.pub_ = None
        self.timer_ = None
        
        self.get_logger().info("Nó GNSS Instanciado. Estado atual: Unconfigured")

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        """Chamado para configurar o hardware (Abrir porta serial do Arduino)"""
        self.get_logger().info("A configurar o hardware serial...")
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            # Cria o publicador de ciclo de vida (só publica se o nó estiver Ativo)
            self.pub_ = self.create_lifecycle_publisher(NavSatFix, '/gps/fix', 10)
            self.get_logger().info("Porta Serial aberta com sucesso.")
            return TransitionCallbackReturn.SUCCESS
        except Exception as e:
            self.get_logger().error(f"Falha ao abrir a porta serial: {e}")
            return TransitionCallbackReturn.FAILURE

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        """Chamado apenas quando o Arduino confirmar o Fix 3D (Trava Lógica)"""
        self.get_logger().info("Nó Ativado! A iniciar telemetria na rede ROS 2 via Zenoh...")
        # Ativa o publicador explicitamente
        super().on_activate(state)
        
        # Inicia a leitura contínua (10Hz)
        self.timer_ = self.create_timer(0.1, self.read_and_publish)
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        """Chamado se o sinal for perdido ou ocorrer elevada EMI"""
        self.get_logger().warn("Nó Desativado! A suspender publicações de telemetria.")
        super().on_deactivate(state)
        
        if self.timer_:
            self.timer_.cancel()
            self.timer_ = None
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        """Fecha conexões limpas e liberta memória"""
        self.get_logger().info("A limpar recursos (fechar porta serial)...")
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.destroy_publisher(self.pub_)
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        """Desligamento total do nó"""
        self.get_logger().info("Desligamento completo do nó GNSS.")
        if self.ser and self.ser.is_open:
            self.ser.close()
        return TransitionCallbackReturn.SUCCESS

    def read_and_publish(self):
        """Função que processa a string serial e constrói a mensagem NavSatFix"""
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                
                # Ignora STATUS ou linhas vazias (Fase de Cold Start do Arduino)
                if line.startswith("STATUS") or line.startswith("Latitude"):
                    return
                
                data = line.split(',')
                # O Arduino envia: Lat,Lon,Alt,Sat,HDOP,Data,Hora
                if len(data) >= 5:
                    msg = NavSatFix()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = 'gps_link'
                    
                    msg.latitude = float(data[0])
                    msg.longitude = float(data[1])
                    msg.altitude = float(data[2])
                    
                    hdop = float(data[4])
                    variance = hdop * hdop
                    msg.position_covariance = [
                        variance, 0.0, 0.0,
                        0.0, variance, 0.0,
                        0.0, 0.0, variance
                    ]
                    msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
                    
                    # Só publica se o nó estiver no estado ACTIVE
                    self.pub_.publish(msg)
                    
            except Exception as e:
                self.get_logger().error(f"Erro ao processar dados: {e}")
                # Aqui poderíamos forçar a transição para ERROR PROCESSING

def main(args=None):
    rclpy.init(args=args)
    node = GNSSLifecycleNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()