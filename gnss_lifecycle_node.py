
#!/usr/bin/env python3
import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from lifecycle_msgs.msg import Transition
from sensor_msgs.msg import NavSatFix
import serial

class GNSSLifecycleNode(Node):
    def __init__(self):
        super().__init__('gnss_edge_node')
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('frame_id', 'gps_link')
        self.declare_parameter('min_satellites', 4)
        self.declare_parameter('max_hdop', 5.0)  
        self.declare_parameter('max_tolerated_errors', 30)

        self.serial_port = self.get_parameter('serial_port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.frame_id = self.get_parameter('frame_id').value
        self.min_satellites = self.get_parameter('min_satellites').value
        self.max_hdop = self.get_parameter('max_hdop').value
        self.max_tolerated_errors = self.get_parameter('max_tolerated_errors').value

        self.ser = None
        self.pub_ = None
        self.timer_ = None
        self.consecutive_errors = 0
        self._degradation_handled = False
        self.get_logger().info("Nó GNSS Instanciado. Estado atual: Unconfigured")

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("A configurar o hardware serial...")
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            self.pub_ = self.create_lifecycle_publisher(NavSatFix, '/gps/fix', 10)
            self.get_logger().info("Porta Serial aberta. A aguardar orquestrador para transição para Ativo.")
            return TransitionCallbackReturn.SUCCESS
        except Exception as e:
            self.get_logger().error(f"Falha ao abrir a porta serial: {e}")
            return TransitionCallbackReturn.FAILURE

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("Nó Ativado! A iniciar monitorização de integridade...")
        super().on_activate(state)
        self.consecutive_errors = 0
        self._degradation_handled = False
        self.timer_ = self.create_timer(0.1, self.read_and_publish)  
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().warn("Nó Desativado! Suspensão forçada das publicações.")
        super().on_deactivate(state)
        if self.timer_:
            self.timer_.cancel()
            self.timer_ = None
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("Limpeza de recursos...")
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.destroy_publisher(self.pub_)
        return TransitionCallbackReturn.SUCCESS
    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("Encerramento total.")
        if self.ser and self.ser.is_open:
            self.ser.close()
        return TransitionCallbackReturn.SUCCESS

    def _handle_sustained_degradation(self):
        if self._degradation_handled:
            return
        self._degradation_handled = True
        self.get_logger().error("ALERTA CRÍTICO: Perda sustentada de fixação GNSS. A transitar para Inactive.")
        try:
            self.trigger_transition(Transition.TRANSITION_DEACTIVATE)
        except Exception as e:
            self.get_logger().error(f"Falha ao auto-desativar o nó: {e}")

    def read_and_publish(self):
        if not (self.ser and self.ser.in_waiting > 0):
            return
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("STATUS") or line.startswith("Latitude"):
                return
            data = line.split(',')
            if len(data) < 5:
                return

            satellites = int(data[3])
            hdop = float(data[4])

            if satellites < self.min_satellites or hdop > self.max_hdop:
                self.consecutive_errors += 1
                self.get_logger().debug(f"Degradação detetada: SATS={satellites}, HDOP={hdop}")
                if self.consecutive_errors >= self.max_tolerated_errors:
                    self._handle_sustained_degradation()
                return 
   
            self.consecutive_errors = 0
            msg = NavSatFix()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            msg.latitude = float(data[0])
            msg.longitude = float(data[1])
            msg.altitude = float(data[2])

            variance = hdop * hdop
            msg.position_covariance = [variance, 0.0, 0.0, 0.0, variance, 0.0, 0.0, 0.0, variance]
            msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
            self.pub_.publish(msg)
        except Exception as e:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = GNSSLifecycleNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass # Fecha de mansinho
    except Exception as e:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
             
                
                
