from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Column, Integer, Float, String, Boolean, Text, case

from database import Base, engine
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import func

#New class representing systems separate from testsets (Allowing revisions to reference an already existing system)
#	System information:		Band;	Type;	Subtype;	SN;
#					Ex.	  ('WR6.5', 'SGX',   '-M',   SGX 804):	WR6.5 SGX-M 804
class System(Base):
	__tablename__ = "system"
	
	SN =		Column(String, primary_key=True, index=True)
	Band =		Column(String(16), nullable=False)
	Type =		Column(String(16), nullable=False)
	Subtype =	Column(String(16), nullable=False)
	Arch =		Column(String(16))
	
	def __repr__(self):
		if self.Arch == None:
			return f"SN {self.SN}: {self.Band} {self.Type}{self.Subtype} {self.SN.replace(self.Band,'').replace(self.Type,'').replace(self.Subtype,'').strip()}"
		else:
			return f"SN {self.SN}: {self.Band} {self.Type}{self.Arch}{self.Subtype} {self.SN.replace(self.Band,'').replace(self.Type,'').replace(self.Arch,'').replace(self.Subtype,'').strip()} - {self.SN}"
	
	def getDict(self):
		return {'SN':self.SN,'Band':self.Band,'Type':self.Type,'Subtype':self.Subtype,'Arch':self.Arch}


#A testset represents a collection of information saved with every single system set of final data
#This table will only hold information pertaining to the order and not the tests
#	Order Information:		Order #;	Customer;	Engineer;	Upload Date;	Approval;
#					Ex.	  ('220196',   'Keysight',   'CXS',     '6/16/2022',      True)
class Testset(Base):
	__tablename__ = "testset"
	
	ID =	Column(Integer, primary_key=True, index=True)
	
	SN1 =	Column(ForeignKey("system.SN"), nullable=False, index=True)
	SN2 =	Column(ForeignKey("system.SN"), index=True)
	rev =	Column(String(16), index=True)
	
	#Order Information
	Order =		Column(String)
	Customer =	Column(String)
	Engineer =	Column(String)
	Last_Edit =	Column(String, nullable=False)
	Approval =	Column(Boolean, nullable=False)
	Deleted =	Column(Boolean, nullable=False, default=False)
	
	Comments = Column(Text)
	
	# Since we're not storing date's in ISO format, we need to do something crafty
	# using sqlalchemy hybrid properties. This will let us filter Testsets by date.
	@hybrid_property
	def datetime(self):
		# @todo: add python parsing of date and time to produce the result
		return datetime.strptime(self.Last_Edit, "%m/%d/%Y %H:%M:%S")

	# This is related to the aforementioned craftiness.
	@datetime.expression
	def datetime(cls):
		# @note: query specific value
		dt_column =(func.substr(cls.Last_Edit, 7, 4) + "-" +
					func.substr(cls.Last_Edit, 1, 2) + "-" +
					func.substr(cls.Last_Edit, 4, 2) + " " +
					func.substr(cls.Last_Edit, 12))

		dt_column = func.datetime(dt_column)
		return dt_column

	def __repr__(self):
		return f"Testset for {self.SN1}" + ('' if self.SN2 is None else f" and {self.SN2}") + f" rev: {self.rev}"
	
	def getDict(self):
		return {'ID':self.ID,'SN1':self.SN1,'SN2':self.SN2,'rev':self.rev,'order':self.Order,
			'customer':self.Customer,'engineer':self.Engineer,'last_edit':self.Last_Edit,'approved':self.Approval,'comments':self.Comments}


#Class representing tests as a link to any file location and then information that will be useful for searching and plotting
#Each unique test type will have an inherited table that has columns with information specific to that test type
class Test(Base):
	__tablename__ = "test"
	
	testsetID =		Column(Integer, ForeignKey("testset.ID"), primary_key=True, index=True)
	test_name =		Column(String, nullable=False, primary_key=True, index=True)
	
	file =			Column(String, nullable=False)
	
	#Spec info
	minimum_spec =	Column(Float)
	min_typ_spec =	Column(Float)
	max_typ_spec =	Column(Float)
	maximum_spec =	Column(Float)
	
	#Test type (ex. TPP)
	test_type =		Column(String)
	
	__mapper_args__ = {'polymorphic_on': test_type, 'polymorphic_identity': 'None'}
	
	def __repr__(self):
		return f"{self.test_name}: {self.file}"
	
	def getDict(self):
		return {'testsetID': self.testsetID, 'test_name': self.test_name, 'file': self.file, 'minimum_spec': self.minimum_spec, 
			'min_typ_spec': self.min_typ_spec, 'max_typ_spec': self.max_typ_spec, 'maximum_spec': self.maximum_spec, 'test_type': self.test_type}
	
	def getSpecDict(self):
		return {'minimum':self.minimum_spec,'min_typ':self.min_typ_spec,'max_typ':self.max_typ_spec,'maximum':self.maximum_spec}


#Test Port Power test
class TPP_Test(Test):
	__tablename__ = "test_port_power_test"
	__mapper_args__ = {'polymorphic_identity': 'TPP'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Harmonics test
class HRM_Test(Test):
	__tablename__ = "harmonics_test"
	__mapper_args__ = {'polymorphic_identity': 'HRM'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Test Port Power test
class UCA_Test(Test):
	__tablename__ = "user_controller_attenuation_test"
	__mapper_args__ = {'polymorphic_identity': 'UCA'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)


#Conversion Loss test
class CL_Test(Test):
	__tablename__ = "conversion_loss_test"
	__mapper_args__ = {'polymorphic_identity': 'CL'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	#IF_offset = Column(Float)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#DANL test
class DANL_Test(Test):
	__tablename__ = "displayed_average_noise_level_test"
	__mapper_args__ = {'polymorphic_identity': 'DANL'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#PXA Sweep test
class PXA_Test(Test):
	__tablename__ = "pxa_sweep_test"
	__mapper_args__ = {'polymorphic_identity': 'PXA'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#IF Bandwidth test
class IF_BW_Test(Test):
	__tablename__ = "if_bandwidth_test"
	__mapper_args__ = {'polymorphic_identity': 'IF_BW'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)


#Dynamic Range test
class DR_Test(Test):
	__tablename__ = "dynamic_range_test"
	__mapper_args__ = {'polymorphic_identity': 'DR'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Input Saturation test
class IS_Test(Test):
	__tablename__ = "input_saturation_test"
	__mapper_args__ = {'polymorphic_identity': 'IS'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Stability test
class SB_Test(Test):
	__tablename__ = "stability_test"
	__mapper_args__ = {'polymorphic_identity': 'SB'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Wave Quantities test
class WQ_Test(Test):
	__tablename__ = "wave_quantities_test"
	__mapper_args__ = {'polymorphic_identity': 'WQ'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Powerlevelability test
class PL_Test(Test):
	__tablename__ = "powerlevelability_test"
	__mapper_args__ = {'polymorphic_identity': 'PL'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Gold Standards test
class GS_Test(Test):
	__tablename__ = "gold_standards_test"
	__mapper_args__ = {'polymorphic_identity': 'GS'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (
		ForeignKeyConstraint(
			['testsetID', 'test_name'],['test.testsetID', 'test.test_name']
		),
	)

#Powerleveling Harmonics test
class PLHRM_Test(Test):
	__tablename__ = "powerleveling_harmonics_test"
	__mapper_args__ = {'polymorphic_identity': 'PLHRM'}
	
	testsetID = Column(Integer, primary_key=True, index=True)
	test_name = Column(String,  primary_key=True, index=True)
	
	__table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#YFactor test
class YFAC_Test(Test):
    __tablename__ = "yfactor_test"
    __mapper_args__ = {'polymorphic_identity': 'YFAC'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Current Sweep test
class CS_Test(Test):
    __tablename__ = "current_sweep_test"
    __mapper_args__ = {'polymorphic_identity': 'CS'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Power Sweep test
class PS_Test(Test):
    __tablename__ = "power_sweep_test"
    __mapper_args__ = {'polymorphic_identity': 'PS'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Current Reliability test
class CRT_Test(Test):
    __tablename__ = "current_reliability_test"
    __mapper_args__ = {'polymorphic_identity': 'CRT'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Power Reliability test
class PRT_Test(Test):
    __tablename__ = "power_reliability_test"
    __mapper_args__ = {'polymorphic_identity': 'PRT'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#DC Oscillation test
class DCO_Test(Test):
    __tablename__ = "dc_oscillation_test"
    __mapper_args__ = {'polymorphic_identity': 'DCO'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Sideband Oscillation test
class SBO_Test(Test):
    __tablename__ = "sideband_oscillation_test"
    __mapper_args__ = {'polymorphic_identity': 'SBO'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Noise Temperature test
class NTEMP_Test(Test):
    __tablename__ = "noise_temperature_test"
    __mapper_args__ = {'polymorphic_identity': 'NTEMP'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

#Generic Gain (can represent Loss) test
class GAIN_Test(Test):
    __tablename__ = "gain_test"
    __mapper_args__ = {'polymorphic_identity': 'GAIN'}
    
    testsetID = Column(Integer, primary_key=True, index=True)
    test_name = Column(String,  primary_key=True, index=True)
    
    __table_args__ = (ForeignKeyConstraint(['testsetID', 'test_name'],['test.testsetID', 'test.test_name']),)

test_type_dict = {'None': Test, 'TPP': TPP_Test, 'HRM': HRM_Test, 'UCA': UCA_Test, 'CL': CL_Test, 'DANL': DANL_Test, 'PXA': PXA_Test, 
				  'IF_BW': IF_BW_Test, 'DR': DR_Test, 'IS': IS_Test, 'SB': SB_Test, 'WQ': WQ_Test, 'PL': PL_Test, 'GS': GS_Test, 'PLHRM': PLHRM_Test, 
				  'YFAC': YFAC_Test, 'CS': CS_Test, 'PS': PS_Test,'CRT': CRT_Test, 'PRT': PRT_Test, 'DCO': DCO_Test, 'SBO': SBO_Test, 'NTEMP': NTEMP_Test,
				  'GAIN': GAIN_Test}

#12/03/24 KDH - following test types need to be added (and defined in models)
#CS - current sweep, PS - power sweep, CRT - current reliability, PRT - power reliability, DCOSC - DC oscillations, SBOSC - sideband oscillation, NTEMP - noise temperature
#GAIN - (generic) gain or loss file

if False:
	connection = engine.connect()
	query = f"ALTER TABLE {'testset'} ADD Comments TEXT ;"
	#query = f"ALTER TABLE {'conversion_loss_test'} DROP IF_offset ;"
	connection.execute(query)

metaobj = Base.metadata
#metaobj.drop_all(engine)
metaobj.create_all(engine)
