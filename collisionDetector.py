#!/usr/bin/env python

import android
import daemon
import argparse
import socket
import signal
import sys


def getArgs():
   parser = argparse.ArgumentParser(description=
                                    'A collision detection daemon',
                                    formatter_class=
                                    argparse.ArgumentDefaultsHelpFormatter)

   parser.add_argument('-i', '--ip', default='192.168.1.217',
                       help='Set the ip of the controller')
   parser.add_argument('-p', '--port', default=23514,
                       help='Set the ip of the controller')
   parser.add_argument('-t', '--threshold', default=10,
                       help="Set accelerometer threshold")
   parser.add_argument('--controller-port', default=23000,
                       help='Set the port of the controller')
   parser.add_argument('-d', '--daemon', default=False, action='store_true',
                       help="Daemonize")

   args = parser.parse_args()

   return args


def main(args):

   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   droid = android.Android(('192.168.1.217', 23514))
   droid.eventClearBuffer()
   droid.startSensingThreshold(2, args.threshold, 2)

   def signal_handler(signal, frame):
      droid.stopSensing()
      sys.exit(0)

   signal.signal(signal.SIGINT, signal_handler)

   while(1):
      print droid.eventWait()
      sock.sendto('setSpeed 0 0', ('localhost', args.controller_port))
   else:
      droid.stopSensing()


if __name__ == '__main__':
   args = getArgs()

   if args.daemon:
      with daemon.DaemonContext():
         main(args)
   else:
      main(args)
