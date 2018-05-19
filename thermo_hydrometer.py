#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

import ConfigParser
import requests
import json
import slackweb

import Adafruit_DHT

def send_to_slack(msg):
    # setup
	inifile = ConfigParser.SafeConfigParser()
	inifilename = '/home/sensor/.slack_config'
	inifile.read(inifilename)
	webhook_url = inifile.get('Thermo-Hydrometer', 'webhookURL')

    # send message
	slack = slackweb.Slack(url=webhook_url)
	slack.notify(text=msg)

def save_to_text(filename, value):
	filename = '/var/tmp/' + filename
	file = open(filename, 'w')

	file.write('{0:0.1f}'.format(value))
	file.close()

def main():
    parser = argparse.ArgumentParser(description='Thermo-Hydrometer utility.')
    parser.add_argument('--sensor', dest='sensor', action='store', help='sensor type', default='2302')
    parser.add_argument('--pin', dest='pin', action='store', help='sensor GPIO pin number', type=int, default=4)
    parser.add_argument('--homebridge', action='store_true', help='ON/OFF Homebridge', default=False)
    parser.add_argument('--slack', action='store_true', help='ON/OFF Slack', default=False)
    parser.add_argument('--debug', action='store_true', help='ON/OFF Slack', default=False)
    args = parser.parse_args()

    # set DHT sensor type
    if args.sensor == '2302':
        sensor = Adafruit_DHT.AM2302
    elif args.sensor == '11':
        sensor = Adafruit_DHT.DHT11
    elif args.sensor == '22':
        sensor = Adafruit_DHT.DHT22
    else:
        msg = u'Error: Invalid sensor type. 11:DHT11, 22:DHT22、2302:AM2302\r\n'
        if args.debug is True: print msg
        send_to_slack(msg)
        return 0
    # set GPIO pin number
    pin = args.pin

    # get temperature & humidity
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if args.debug is True:
        print temperature
        print humidity

    if temperature is None or humidity is None:
        # generate Error message
        msg = u'Error: Measurement could not be done\r\n'
        send_to_slack(msg)
    else:
        if args.homebridge is True: # for Homebridge
            filename_temp = 'homebridge_now_temp.txt'
            save_to_text(filename_temp, temperature)
            filename_humi = 'homebridge_now_humidity.txt'
            save_to_text(filename_humi, humidity)
        if args.slack is True: # for Slack
            # generate message
            msg = u'現在の室温は{0:0.1f}*C、湿度は{1:0.1f}%です。'.format(temperature, humidity)
            if temperature >= 35:
                msg += u' [危険]'
            elif temperature >= 31 and temperature < 35:
                msg += u' [厳重警戒]'
            elif temperature >= 28 and temperature < 31:
                msg += u' [警戒]'
            elif temperature >= 24 and temperature < 28:
                msg += u' [注意]'
            msg += '\r\n'
            # send message via slack
            send_to_slack(msg)


if __name__ == '__main__':
    main()