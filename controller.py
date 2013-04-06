#!/usr/bin/python

import android
import time
import socket
import json
import argparse
import select
import signal
import sys
import daemon
import motor_i2c


def signal_handler(signal, frame):
   print 'Exiting'
   sys.exit(0)


def getArgs():
   parser = argparse.ArgumentParser(description=
                                    'Setup Telemetry and Command System')

   parser.add_argument('-p', '--sendPort', default=23000,
                       help='Set the send port for telemetry')
   parser.add_argument('-a', '--sendIP', default='192.168.1.255',
                       help='Set the send port for telemetry')
   parser.add_argument('-l', '--listenPort', default=23001,
                       help='Set the send port for telemetry')
   parser.add_argument('-i', '--interval', default=2000.0,
                       help="Interval to read sensors in ms")
   parser.add_argument('-d', '--daemon', default=False, action='store_true',
                       help="Daemonize")
   parser.add_argument('-P', '--phone-ip', default='dk-phone',
                       help="Set the IP of the phone")
   parser.add_argument('--phone-port', default='23514',
                       help="Set the port of the phone")

   args = parser.parse_args()

   return args


def main(args):
   signal.signal(signal.SIGINT, signal_handler)

   # Setup command and control
   commandPort = args.listenPort
   commandSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   commandSocket.bind(('', commandPort))
   commandSocket.setblocking(0)

   # Setup network telemetry
   telemetryPort = args.sendPort
   telemetrySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   telemetryIP = args.sendIP
   if telemetryIP == '192.168.1.255':
      telemetrySocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
   interval = args.interval

   # Initialize Bus
   bus = motor_i2c.setupSMBus()

   # Setup file recording
   data_fd = file('sensor_data.txt', 'w')

   # Setup phone
   phoneIP = args.phone_ip
   phonePort = args.phone_port
   try:
      droid = android.Android((phoneIP, phonePort))
      droid.startSensingTimed(1, 500)
   except:
      droid = None

   lastSensorRead = 0.0
   while(1):
      if (time.time() - lastSensorRead) > (interval / 1000.0) and droid:
         sensors = droid.readSensors().result
         sensors_str = json.dumps(sensors)
         data_fd.write(sensors_str)
         data_fd.flush()
         telemetrySocket.sendto(sensors_str, (telemetryIP, telemetryPort))
         lastSensorRead = time.time()
      elif droid is None:
         lastSensorRead = time.time()

      waitTime = (interval / 1000.0) - (time.time() - lastSensorRead)
      (inputReady,
       outputReady,
       errReady) = select.select([commandSocket],
                                 [],
                                 [],
                                 waitTime)
      msg = ''
      for sock in inputReady:
         if sock == commandSocket:
            msg, addr = commandSocket.recvfrom(4096)

      issueCmd(msg, bus)

   else:
      data_fd.close()

   return


def issueCmd(msg, bus):
   """
      message formats

      COMMAND      Options

      setSpeed     speedA speedB
      setHeading   ?

      Commands are space separated strings
   """

   if msg == '':
      return

   msg = msg.split(' ')
   command = msg[0]
   options = msg[1:]

   commands = {'setSpeed': setSpeed,
               'setHeading': setHeading}

   result = commands[command](options, bus)

   return result


def setSpeed(speed, bus):
   try:
      speedA = int(speed[0])
      speedB = int(speed[1])
      motor_i2c.SetMotorSpeed(speedA, speedB, bus)
   except:
      print 'Failure setting speed'
      print sys.exc_info()


def setHeading(heading, bus):
   pass


if __name__ == '__main__':
   args = getArgs()

   if args.daemon:
      with daemon.DaemonContext():
         main(args)
   else:
      main(args)
