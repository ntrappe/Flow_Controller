import sys
import numpy as np
import pandas as pd

## Helper functions
##----------------------------------------------------------------------------
## Name: saturated_vapor_pressure
## Function: gives the pressure of water vapor in air in hPa in 100% humidity
## Inputs: air_temp - temperature of air in Celsius
##----------------------------------------------------------------------------
def saturated_vapor_pressure(air_temp):
  return 6.1078 * 10 ** (7.5 * air_temp/(air_temp + 237.3)) 


##----------------------------------------------------------------------------
## Name: actual_vapor_pressure
## Function: multiplies saturated pressure by relative humidity (hPa)
## Inputs: saturated_pressure - water vapor pressure at dew point in hPa
##         humidity - relative humidity (%s)
##----------------------------------------------------------------------------
def actual_vapor_pressure(saturated_pressure, humidity):
  relative_humidity = humidity / 100.0
  return saturated_pressure * relative_humidity 


##----------------------------------------------------------------------------
## Name: dry_air_pressure
## Function: gives pressure of dry air in hPa
## Inputs: actual_vapor_pressure - water vapor pressure per the humidity
##         air_pressure - total air pressure (assumed at 0 ft sealevel)
##----------------------------------------------------------------------------
def dry_air_pressure(actual_vapor_pressure, air_pressure):
  return air_pressure - actual_vapor_pressure


## Big function
##----------------------------------------------------------------------------
## Name: air_density
## Function: calculates the air dernsity as kg/m^3
## Inputs: dry_air_pressure - pressure of dry air (hPa)
##         vapor_pressure - (actual) pressure of water vapor (hPa)
##         temp - air temperature in Kelvin
##----------------------------------------------------------------------------
def air_density(dry_air_pressure, vapor_pressure, temp):
  return dry_air_pressure/(287.05831*temp) + vapor_pressure/(461.4964*temp)


##----------------------------------------------------------------------------
## Name: actual_specific_heat
## Function: calculates the specific heat of a gas as it changes due to temp
## Inputs: specific_heat_capacity - the starting specific heat at 0 deg C 
##                                  of a gas (CP cal/deg C)
##         temp - air temperature
## Note: equation only derived from analyzing changes in air heat capacity
##       in response to temperature from the range [0,30]
##----------------------------------------------------------------------------
def actual_specific_heat(specific_heat_capacity, temp):
  return 6.429 * 10**(-6) * temp + specific_heat_capacity


##----------------------------------------------------------------------------
## Name: get_GCF
## Function: calculate the gas correction factor that the Mass Flow Controller
##           uses to determine the flow as a ratio to the calibrated gas
## Inputs: density - density of the gas (g/l)
##         spec_heat - specific heat (cp) of gas (cal/g degrees C)
##----------------------------------------------------------------------------
def conversion_factor(density, spec_heat):
  return (0.3106 * 1 * correction_factor)/(1 * density * spec_heat) 


##----------------------------------------------------------------------------
## Name: set_flow
## Function: based on the effects of humidity and temperature on the flow,
##           we need to account for that change by setting the flow above
##           or below the baseline to compensate
## Inputs: GCF - the gas conversion factor that Mass Flow Controller uses
##               to determine the flow as a ratio to the calibrated gas
##         baseline - the flow you'd like the gas to move at (sccm)
##----------------------------------------------------------------------------
def set_flow(GCF, baseline):
  actual_flow = GCF * 100
  # if actual flow is greater/less than the wanted flow, adjust it to be
  # less/greater than it to the same degree
  if actual_flow > baseline:
    return baseline - (actual_flow - baseline)
  elif actual_flow < baseline:
    return baseline + (baseline - actual_flow)

  
##----------------------------------------------------------------------------
## Name: command_line
## Function: parses any user given input and will provide the default if none
##           is given, also includes error checks
## Inputs: param_name - name of the parameter (ex. humidity)
##         metrics - the units of the parameter (ex. decimal, hPa)
##         example - example of what to input
##         _min - minimum value the parameter should be
##         _max - maximum value the parameter should be
##         default - default value for the parameter
##----------------------------------------------------------------------------
def command_line(param_name, metrics, example, _min, _max, default):
  while True:
    # try to get the user's input, otherwise, use defaults
    try:
      response = raw_input('\nEnter the ' + param_name + ' as a ' + metrics 
                           + '; ex: ' + example + '\n> ')
      # did get a response
      if response != '': 
	# parse temperature as float and check range of air temperature
	param = float(response)
	if param < _min or param > _max:
	  print('\t' + param_name + ' out of range [' + str(_min) + ',' + 
                str(_max) + '], will use default of ' + str(default))
	return param

      # no response given so give default message
      else:
	print('\t No ' + param_name + ' given, will use default of '
              + str(default))
	return default

    except EOFError:
      print('\t\n Stopping . . .\n')
      break
    except KeyboardInterrupt:
      print('\t\n Stopping . . .\n')
      break


def command_line_gas_name(param_name, example, default):
  while True:
    # try to get user input otherwise use defaults
    try:
      response = raw_input('Enter the ' + param_name + '; ex: ' + example
				 + '\n> ')
      # user did give a response so try to parse (see if find a match)
      if response != '':
	if find_gas(response) is False:
	  print('\tThe gas <' + response + '> was not found, will use '
		  'default of ' + default)
	return response

      # no response given so set up default values for Air
      else: 
	print('\t No ' + param_name + ' given, will use default of ' 
	      + str(default))
        find_gas('air')
        return default

    except EOFError:
      print('\t\n Stopping . . .\n')
    except KeyboardInterrupt:
      print('\t\n Stopping . . .\n')


## Helper function called by command_line
##----------------------------------------------------------------------------
## Name: find_gas
## Function: looks to see if the desired gas exists in the Mass Flow Controller
##           and will collect the gas' specific heat and correction factor for
##           its molecular structure
## Inputs: param_name - name of the gas (ex. air)
##----------------------------------------------------------------------------
def find_gas(param_name):
  global _specific_heat, correction_factor

  data = pd.read_csv('gas_data.csv', delimiter=',')
  gas_names = np.array(data[['Gas Name']], dtype=str)
  gas_symbols = np.array(data[['Symbol']], dtype=str)

  # iter thru rows in the matrix of gas names and symbols to find match
  for row in range(gas_names.size):

    # if we do match the gas name or symbol, then save the specific
    # heat and correction factor and return true (was found)
    if param_name.lower() in (gas.lower() for gas in gas_names[row]):
      _specific_heat = data['Specific Heat'].iloc[row]
      correction_factor = data['Correction Factor'].iloc[row]
      return True

  # did not find a match
  specific_heat = 0.240
  correction_factor = 1.030
  return False
  

## Main driver
##----------------------------------------------------------------------------
## Name: __init__
## Function: calls the individual functions to calculate pressures,
##           actual heat, then density, then GCF, and then the flow
## Inputs: gas - the gas name (default to air)
##         temp_C - temperature in Celsius (default 20)
##         humidity - relative humidity (default 50 for 50%)
##         air_pressure - pressure at sea level (default 760 mmHg)
##         user_flo - desired flow rate for the gas to actual be at
##----------------------------------------------------------------------------
def __init__(gas='air', temp_C=15, humidity=50, user_flo=100, air_pressure=760):
  global _density, _GCF, _actual_heat, _flow

  # conversions
  temp_K = temp_C + 273.15
  air_pressure_hPa = air_pressure * 1.333

  # get the water vapor pressure in hPa
  vapor_pressure = saturated_vapor_pressure(temp_C)
  actual_pressure = actual_vapor_pressure(vapor_pressure, humidity)
  dry_air = dry_air_pressure(actual_pressure, air_pressure_hPa)

  # calculate the density of the gas in kg/m^3
  _density = air_density(dry_air, actual_pressure, temp_K)
  _density *= 100

  # calculate the specific heat of the gas 
  _actual_heat = actual_specific_heat(_specific_heat, temp_C)

  # calculate the Gas Conversion Factor and flow ajustment from that
  _GCF = conversion_factor(_density, _actual_heat)
  _flow = set_flow(_GCF, user_flo)
 

## Call the functions
print('\n=====================================================')
print('\t\t FLOW CALCULATOR ')
print('=====================================================\n')

user_gas = command_line_gas_name('gas name', 'Chlorine or Cl2', 'Air')
user_temp = command_line('temperature', 'number in degrees C', 
                         '10 for 10 degrees C', 0, 30, 15)
user_humidity = command_line('humidity', 'number', '50 for 50%', 0, 100, 50)
user_flow = command_line('desired flow rate', 'number in sccm', '100 sccm',
                          0, 1200, 100)

# give the driver the user inputs
__init__(user_gas, user_temp, user_humidity, user_flow)

print('\n----------------------------------------------------\n')
print('  SET GAS FLOW TO: ' + str(_flow) + ' sccm\n')
print('  Gas name: \t' + str(user_gas))
print('  Temperature: \t' + str(user_temp))
print('  Humidity: \t' + str(user_humidity))
print('  Desired Flow:\t' + str(user_flow))
print('  Density: \t' + str(_density))
print('  GCF: \t\t' + str(_GCF))
print('\n=====================================================\n')


