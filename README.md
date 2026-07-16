# Chat con Cifrado de Extremo a Extremo (E2EE)

Una arquitectura de mensajería asíncrona cliente-servidor que implementa criptografía de curva elíptica (ECC) y validación de llaves asimétricas con RSA desde cero, prescindiendo de capas o protocolos de terceros.

## Características Principales

- **Privacidad y Confidencialidad:** Los mensajes viajan completamente encriptados de extremo a extremo utilizando ECC.
- **Validación de Identidad:** Verificación de llaves asimétricas mediante RSA para prevenir ataques de intermediario (Man-in-the-Middle).
- **Comunicación en Tiempo Real:** Arquitectura de red orientada a concurrencia utilizando Sockets TCP para mantener canales bidireccionales estables entre pares.
- **Implementación Nativas:** Toda la lógica criptográfica y de manejo de red (sockets) fue desarrollada de manera nativa sin frameworks de alto nivel.

## Arquitectura

El sistema se compone de dos componentes principales:
1. **Servidor Relay:** Se encarga de gestionar la concurrencia y recibir las conexiones entrantes mediante sockets. Funciona como un enrutador que toma los paquetes encriptados y los retransmite a su destino correspondiente (Zero-Knowledge: el servidor no tiene capacidad para desencriptar ni leer los mensajes).
2. **Cliente (Core):** Maneja el flujo criptográfico local: generación de llaves, el cifrado y descifrado de mensajes, y la persistencia de una sesión asíncrona segura con el servidor y los demás nodos de la red.

## Tecnologías y Conceptos Aplicados
- **Lenguaje:** Python
- **Redes:** Programación con Sockets TCP
- **Criptografía:** Elliptic Curve Cryptography (ECC), RSA
