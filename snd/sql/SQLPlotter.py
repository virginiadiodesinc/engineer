import plotly.express as px
from util.FileReader import readFile
import pandas as pd


class SQLPlotter:

	def __init__(self, sql_result, data_index=0, data_name='file', index_index=1):
		#this is kind of overkill, I think the data_name will always be 'file'
		self.data = []
		self.indices = []
		for row in sql_result:
			data = getattr(row[data_index], data_name)
			self.data.append(data)
			index = row[index_index]
			self.indices.append(index)

	def readTPPFiles(self):
		
		dflist = []
		for k,j in zip(self.data,self.indices):
			df = readFile(k)
			df['id'] = j
			dflist.append(df)


		alldfs = pd.concat(dflist)
		self.df = alldfs
		return alldfs,dflist

	def scatterPlot(self):
		px.scatter(y=self.df['Source (dBm)'], x=self.df.index, color=self.df['id'])