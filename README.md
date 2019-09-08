# smart-neighborhood-simulator

Quickly define and deploy smart neighborhood simulations.

## Getting Started

### Prerequisites
1. Install Flask:
    ```pip install Flask```
2. Ready to go!

## Usage:
1. Navigate to the ```smart-neighborhood-simulator/``` directory
2. In a terminal, run ```python3 api.py```
3. Navigate to http://127.0.0.1:5000/ in a web browser
4. Set up the parameters of the simulation (i.e., number of houses)

## Interacting with the homes
Homes can be interacted with in one of two ways:

####Method One:
In a separate tab or window, navigate to:
```
http://127.0.0.1:5000/dev/{device}/{args}/{neighborhood_id}/{house_id}
```

   1. The {device} argument can be:
	    - thermostat
    	- evcs
    	- pool_pump
   2. Potential arguments include:
	    - target=[int]
	- heat/cool
	- on/off

    Example: 
	
	http://127.0.0.1:5000/dev/thermostat/target=76_heat_on/0/  --  sets the mode, fan, and target temperature of each house in neighborhood 0 
	
	
####Method Two:
   An automated controller script can be written. Check under the ```controller.py``` file for more information.

## Design
A diagram of the world and modules can be found under the ```docs/``` folder. The diagram 