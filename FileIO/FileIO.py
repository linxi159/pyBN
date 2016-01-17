import json

class BNio:

	def __init__(self, BN):
		self.BN = BN

	def read(self, filepath):
		form = filepath.split('.')[-1].lower()
		if form == 'bif':
			self.read_bif(filepath)
		elif form == 'bn':
			self.read_libpgm(filepath)

	def write(self, filepath):
		"""
		This function writes a BKB object to a .bkbn file

		Arguments:
			1. *filename* - the path/name of the file to which the function will write the BKB object.
		"""
		total_dump = {"Vdata":self.BN.data, "V": self.BN.V, "E": self.BN.E}
		with open(filepath, 'w') as outfile:
			json.dump(total_dump, outfile,indent=2)
		del total_dump

	def read_bif(self, filepath='pyBN/data/asia.bif'):
		"""
		This function reads a .bif file into a BN object

		"""
		V = []
		E = []
		data = {}

		with open(filepath, 'r') as f:
			while True:
				line = f.readline()
				if 'variable' in line:
					new_vertex = line.split()[1]
					V.append(new_vertex) # add to self.BN.V
					data[new_vertex] = {} # add empty dict to self.BN.data
					new_line = f.readline()
					new_vals = new_line.replace(',', ' ').split()[6:-1] # list of vals
					data[new_vertex]['vals'] = new_vals # add vals to self.BN.data dict
					data[new_vertex]['numoutcomes'] = len(new_vals)
					data[new_vertex]['children'] = []
					data[new_vertex]['cprob'] = []
				elif 'probability' in line:
					line = line.replace(',', ' ')
					child_rv = line.split()[2]
					parent_rvs = line.split()[4:-2]
					num_tail = len(parent_rvs)
					if num_tail == 0: # prior
						data[child_rv]['parents'] = []
						new_line = f.readline().replace(';', ' ').replace(',',' ').split()
						prob_values = new_line[1:]
						data[child_rv]['cprob'] = map(float,prob_values)
					else: # not a prior
						data[child_rv]['parents'] = list(parent_rvs)
						for parent in parent_rvs:
							E.append([parent,child_rv])
							data[parent]['children'].append(child_rv)
						while True:
							new_line = f.readline()
							if '}' in new_line:
								break
							new_line = new_line.replace(',',' ').replace(';',' ').replace('(', ' ').replace(')', ' ').split()
							prob_values = new_line[-(data[new_vertex]['numoutcomes']):]
							prob_values = map(float,prob_values)
							data[child_rv]['cprob'].append(prob_values)
				if line == '':
					break

		self.BN.V = V
		self.BN.E = E
		self.BN.data = data

	def read_libpgm(self, filepath='data/cmu.bn'):
		"""
		This function reads in a libpgm-style format into a BN object

		File Format:
			{
			    "V": ["Letter", "Grade", "Intelligence", "SAT", "Difficulty"],
			    "E": [["Intelligence", "Grade"],
			        ["Difficulty", "Grade"],
			        ["Intelligence", "SAT"],
			        ["Grade", "Letter"]],
			    "Vdata": {
			        "Letter": {
			            "ord": 4,
			            "numoutcomes": 2,
			            "vals": ["weak", "strong"],
			            "parents": ["Grade"],
			            "children": None,
			            "cprob": [[.1, .9],[.4, .6],[.99, .01]]
			        },
			        ...
			}
		"""
		def byteify(input):
			if isinstance(input, dict):
				return {byteify(key):byteify(value) for key,value in input.iteritems()}
			elif isinstance(input, list):
				return [byteify(element) for element in input]
			elif isinstance(input, unicode):
				return input.encode('utf-8')
			else:
				return input

		V = []
		E = []
		data = {}
		f = open(filepath,'r')
		ftxt = f.read()

		success=False
		try:
			data = byteify(json.loads(ftxt))
			self.BN.V = data['V']
			self.BN.E = data['E']
			self.BN.data = data['Vdata']
			success = True
		except ValueError:
			pass

		if not success:
			#print 'Cleaning up format..','\n'
			try:
				ftxt = ftxt.translate(None,'\n')
				ftxt = ftxt.translate(None,'\t')
				ftxt = ftxt.replace(':', ': ')
				ftxt = ftxt.replace(',', ', ')
				ftxt = ftxt.replace('None', 'null')
				#ftxt = ftxt.replace('.', '0.')
				data = byteify(json.loads(ftxt))
				self.BN.V = data['V']
				self.BN.E = data['E']
				self.BN.data = data['Vdata']
			except ValueError:
				raise ValueError, 'JSON Conversion failed. Check Formatting.'
		f.close()

		assert isinstance(data, dict), 'JSON Conversion Failed - Check filevar.'