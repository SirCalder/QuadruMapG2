#include <TinyGPS++.h>
#include <SoftwareSerial.h>

// ==============================================================================
// CONFIGURAÇÕES DE HARDWARE (Elegoo Uno R3 + Quectel L30)
// ==============================================================================
const int RX_PIN = 2;       // Ligar ao TX do módulo Quectel
const int TX_PIN = 3;       // Ligar ao RX do módulo Quectel
const int WAKEUP_PIN = 4;   // Ligar ao pino AN para a ignição eletrônica

// Taxas de transmissão 
const uint32_t GPS_BAUD = 4800;   // A taxa real do Quectel L30!
const uint32_t PC_BAUD = 115200;  // Comunicação rápida com a Jetson/ROS 2

TinyGPSPlus gps;
SoftwareSerial portaGPS(RX_PIN, TX_PIN);

unsigned long ultimoAviso = 0;

void setup() {
  Serial.begin(PC_BAUD);
  
  // Rotina de Ignição do Quectel L30
  pinMode(WAKEUP_PIN, OUTPUT);
  digitalWrite(WAKEUP_PIN, HIGH);
  delay(500); 
  digitalWrite(WAKEUP_PIN, LOW);
  
  portaGPS.begin(GPS_BAUD);
  
  // Informa ao ROS 2 que o Arduino iniciou (O Python ignora linhas com "STATUS")
  Serial.println("STATUS,Edge Computing GNSS Iniciado.");
}

void loop() {
  // Alimenta o objeto TinyGPS++ com os dados puros (NMEA)
  while (portaGPS.available() > 0) {
    gps.encode(portaGPS.read());
  }

  // ==============================================================================
  // PROCESSAMENTO NA BORDA (EDGE COMPUTING)
  // Só envia para a Jetson se a localização foi atualizada e for válida
  // ==============================================================================
  if (gps.location.isValid() && gps.location.isUpdated()) {
    
    // FORMATO ESPERADO PELO ROS 2: Lat,Lon,Alt,Sat,HDOP,Data,Hora
    
    Serial.print(gps.location.lat(), 6); Serial.print(",");
    Serial.print(gps.location.lng(), 6); Serial.print(",");
    
    if (gps.altitude.isValid()) {
      Serial.print(gps.altitude.meters(), 1);
    } else {
      Serial.print("0.0");
    }
    Serial.print(",");
    
    Serial.print(gps.satellites.value()); Serial.print(",");
    
    // Adição vital do HDOP para o Filtro de Kalman do ROS 2
    if (gps.hdop.isValid()) {
      Serial.print(gps.hdop.hdop(), 2); 
    } else {
      Serial.print("99.9"); // Valor alto de erro se não for válido
    }
    Serial.print(",");
    
    // Data
    if (gps.date.isValid()) {
      if (gps.date.day() < 10) Serial.print("0"); Serial.print(gps.date.day()); Serial.print("/");
      if (gps.date.month() < 10) Serial.print("0"); Serial.print(gps.date.month()); Serial.print("/");
      Serial.print(gps.date.year());
    } else {
      Serial.print("00/00/0000");
    }
    Serial.print(",");
    
    // Hora
    if (gps.time.isValid()) {
      if (gps.time.hour() < 10) Serial.print("0"); Serial.print(gps.time.hour()); Serial.print(":");
      if (gps.time.minute() < 10) Serial.print("0"); Serial.print(gps.time.minute()); Serial.print(":");
      if (gps.time.second() < 10) Serial.print("0"); Serial.print(gps.time.second());
    } else {
      Serial.print("00:00:00");
    }
    
    Serial.println(); // Quebra de linha para a Jetson ler
    
  } else {
    // Feedback visual a cada 2 segundos enquanto não tem satélites
    if (millis() - ultimoAviso > 2000) {
      Serial.println("STATUS,Aguardando_Fix_GNSS...");
      ultimoAviso = millis();
    }
  }
}
