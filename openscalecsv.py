# -*- coding: utf-8 -*-

import os, sys, datetime, csv

class OpenScaleCSV(object):

	def __init__(self):

		self.items = []

	def __parsedate__(self, ds):

		dsa = ds.replace(':', ' ').replace('/', ' ').replace('-', ' ').replace('.', ' ').replace('  ', ' ').split(' ')
		if ((int(dsa[2]) > 31) & (int(dsa[0]) <= 31)):
			tmp = dsa[0]
			dsa[0] = dsa[2]
			dsa[2] = tmp
		while len(dsa) < 6:
			dsa.append('0')
		return datetime.datetime(int(dsa[0]), int(dsa[1]), int(dsa[2]), int(dsa[3]), int(dsa[4]), int(dsa[5]))

	def load(self, filename):

		headers = []
		with open(filename, 'r') as fp:
			csvreader = csv.reader(fp, delimiter=',', quotechar='"')
			for row in csvreader:
				if len(headers) == 0:
					headers = row
					continue
				item = {}
				for i in range(0, len(row)):
					key = headers[i]
					value = row[i]
					if key == 'dateTime':
						value = self.__parsedate__(value)
						item[key] = value
						continue
					if key == 'comment':
						item[key] = value
						continue
					value = float(value)
					if value != 0.0:
						item[key] = value
				self.items.append(item)

	def records(self):

		return len(self.items)

	def record(self, ix):

		return self.items[ix]
