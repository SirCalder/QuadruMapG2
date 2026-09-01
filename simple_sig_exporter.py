#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import json
import os
import datetime

class SimpleSIGExporter(Node):
    def __init__(self):
        super().__init__('simple_sig_exporter')
        self.coordinates = []
        self.subscription = self.create_subscription(
            NavSatFix, '/gps/fix', self.gps_callback, 10)
        self.get_logger().info("Nó Consumidor SIG iniciado. À espera de dados validados...")

    def gps_callback(self, msg):
        self.coordinates.append([msg.longitude, msg.latitude])
        self.get_logger().info(f"Recebido: Lon {msg.longitude:.5f}, Lat {msg.latitude:.5f} | Total: {len(self.coordinates)}")

    def save_geojson(self):
        if not self.coordinates:
            self.get_logger().warn("Nenhum dado recebido. Nada a guardar.")
            return

        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": { "type": "LineString", "coordinates": self.coordinates },
                "properties": { "name": "Trajetoria_JetTank", "pontos_validados": len(self.coordinates) }
            }]
        }

        filename = f"trajetoria_jettank_{datetime.datetime.now().strftime('%H%M%S')}.geojson"
        filepath = os.path.join('/ros2_ws/src', filename) 
        with open(filepath, 'w') as f:
            json.dump(geojson_data, f, indent=4)
        self.get_logger().info(f"SUCESSO! Mapa guardado em: {filepath}")

def main(args=None):
    rclpy.init(args=args)
    node = SimpleSIGExporter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.save_geojson()
        pass # Fecha de mansinho
    except Exception as e:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()











































































































































































































































































































































































































































































































































































































































#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import json
import os
import datetime

class SimpleSIGExporter(Node):
    def __init__(self):
        super().__init__('simple_sig_exporter')
        self.coordinates = [] # Buffer de memória
        
        # Subscreve o tópico protegido gerado pelo Lifecycle Node
        self.subscription = self.create_subscription(
            NavSatFix, 
            '/gps/fix', 
            self.gps_callback, 
            10
        )
        self.get_logger().info("Nó Consumidor SIG iniciado. À espera de dados validados...")

    def gps_callback(self, msg):
        # O GeoJSON exige o formato [Longitude, Latitude]
        self.coordinates.append([msg.longitude, msg.latitude])
        
        # Feedback visual para sabermos que os dados estão a chegar
        self.get_logger().info(f"Recebido: Lon {msg.longitude:.5f}, Lat {msg.latitude:.5f} | Total de Pontos: {len(self.coordinates)}")

    def save_geojson(self):
        if not self.coordinates:
            self.get_logger().warn("Nenhum dado recebido. Nada a guardar.")
            return

        # Estrutura padrão de um GeoJSON do tipo Linha (LineString)
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self.coordinates
                    },
                    "properties": {
                        "name": "Trajetoria_JetTank",
                        "pontos_validados": len(self.coordinates)
                    }
                }
            ]
        }

        # Cria um nome de ficheiro único
        filename = f"trajetoria_jettank_{datetime.datetime.now().strftime('%H%M%S')}.geojson"
        
        # Guarda na pasta mapeada com o Docker para aparecer no JetTank real
        filepath = os.path.join('/ros2_ws/src', filename) 

        with open(filepath, 'w') as f:
            json.dump(geojson_data, f, indent=4)

        self.get_logger().info(f"SUCESSO! Mapa guardado em: {filepath}")

def main(args=None):
    rclpy.init(args=args)
    node = SimpleSIGExporter()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Quando pressionar Ctrl+C no Terminal 2, ele guarda o ficheiro e sai
        node.save_geojson()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
