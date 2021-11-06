import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from serial import Serial


class LelitServer(HTTPServer):
    def __init__(self, serial_port, serial_baudrate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor = Serial(serial_port, serial_baudrate, timeout=1)

    def get_sensor_data(self):
        self.sensor.flushInput()
        raw_data = self.sensor.readline()
        raw_data = self.sensor.readline()

        return self.__parse_sensor_data__(str(raw_data))

    @staticmethod
    def __parse_sensor_data__(data):
        if not data or len(data) < 10:
            return {}

        data = str(data).split(',')
        return {
            'version': data[0][2:],
            'steam': int(data[1]),
            'steam_target': int(data[2]),
            'heat_exchanger': int(data[3]),
            'fast_heating_countdown': int(data[4]),
            'heating': data[5][0] == '1',
        }


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = self.server.get_sensor_data()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {e}'.encode())
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        return

    def do_POST(self):
        return


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--host', default='localhost', help='Hostname to serve from')
    arg_parser.add_argument('--port', type=int, default=8000, help='Port number on which to listen')
    arg_parser.add_argument('--serial-port', default='/dev/ttyUSB0', help='Serial port to read from')
    arg_parser.add_argument('--serial-baudrate', type=int, default=9600, help='Serial baudrate')
    args = arg_parser.parse_args()

    server = LelitServer(args.serial_port, args.serial_baudrate, (args.host, args.port), RequestHandler)

    print(f'Listening on {args.host}:{args.port}')
    server.serve_forever()
