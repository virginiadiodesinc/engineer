#===========================================================================================================
#= SQLAlchemy module
#= 3/18/2022
#= CXS

from specs import BAND_SETTINGS, SPEC_DICT

SSP_DB_FILE = "W:/Engineer/CXS/DBcomments/vdi_ssp/sql/db/SSP_DB.db"
SSP_DB_DATA_DIR = "W:/Python3/vdi_ssp/sql/db/files"#SSP_DB_DATA_DIR = "W:/CXS/vdi_ssp_dev/vdi_ssp/sql/db/files"

SSP_DB_FILE = "W:/Python3/vdi_ssp/sql/db/SSP_DB.db"
SSP_DB_DATA_DIR = "W:/Python3/vdi_ssp/sql/db/files"

#Used to sort tables by column
BANDS = list(BAND_SETTINGS.columns)
SYSTEMS = list(SPEC_DICT['Test Requirements'].keys())

ORDERS = {'band': BANDS, 'type': SYSTEMS}
#Have to turn them into dicts because order_by(case(...))
for order in ORDERS:	ORDERS[order] = {item:ind for ind, item in enumerate(ORDERS[order].copy())}

'''
#Band specifications dict holding all in-band frequencies
BAND_specs = {'WR28':{'start':26,'stop':40},
			  'WR22':{'start':33,'stop':50},
			  'WR19':{'start':40,'stop':60},
			  'WR15':{'start':50,'stop':75},
			  'WR12':{'start':60,'stop':90},
			  'WR10':{'start':75,'stop':110},
			  'WR9.0':{'start':82,'stop':125},
			  'WR8.0':{'start':90,'stop':140},
			  'WR6.5':{'start':110,'stop':170},
			  'WR5.1':{'start':140,'stop':220},
			  'WR4.3':{'start':170,'stop':260},
			  'WR3.4':{'start':220,'stop':330},
			  'WR2.8':{'start':260,'stop':400},
			  'WR2.2':{'start':330,'stop':500},
			  'WR1.5':{'start':500,'stop':750},
			  'WR1.0':{'start':750,'stop':1100},
			  'WR0.65':{'start':1100,'stop':1500}}
'''