import flask
from world import World
import os
import json

app = flask.Flask(__name__)
world = None


def c2f(temp):
    c_temp = temp * 9.0 / 5.0 + 32.0
    return c_temp


def f2c(temp):
    f_temp = (temp - 32.0) * 5.0 / 9.0
    return f_temp

# landing page
@app.route('/', methods=['GET'])
def home():
	return flask.render_template('mainpage.html')


# simulation setup
@app.route('/world/params', methods=['POST'])
def setup_world(num_ngh_=None, num_homes_=None, run_time_=None, lower_t_=None, upper_t_=None,
				min_length_=None, max_length_=None, min_width_=None, max_width_=None):
	global world
	abs_path, filename = os.path.split(os.path.realpath(__file__))

	if num_ngh_ is not None:
		num_ngh = int(num_ngh_)
	else:
		num_ngh = int(flask.request.form['num_ngh'])

	if num_homes_ is not None:
		num_homes = int(num_homes_)
	else:
		num_homes = int(flask.request.form['num_homes'])

	if run_time_ is not None:
		run_time = int(run_time_)
	else:
		run_time = int(flask.request.form['run_time']) * 3600  # hours to seconds

	if lower_t_ is not None:
		lower_t = int(lower_t_)
	else:
		lower_t = int(flask.request.form['lower_t'])

	if upper_t_ is not None:
		upper_t = int(upper_t_)
	else:
		upper_t = int(flask.request.form['upper_t'])

	if min_length_ is not None:
		min_length = int(min_length_)
	else:
		min_length = int(flask.request.form['min_length'])

	if max_length_ is not None:
		max_length = int(max_length_)
	else:
		max_length = int(flask.request.form['max_length'])

	if min_width_ is not None:
		min_width = int(min_width_)
	else:
		min_width = int(flask.request.form['min_width'])

	if max_width_ is not None:
		max_width = int(max_width_)
	else:
		max_width = int(flask.request.form['max_width'])

	season = flask.request.form['season']
	weather = flask.request.form['weather']

	logging_dir = "{}/logging/".format(abs_path)
	if not os.path.isdir(logging_dir):
		os.makedirs(logging_dir)
	
	data_dir = "{}/data/".format(abs_path)
	if not os.path.isdir(data_dir):
		os.makedirs(data_dir)

	log = True
	world = World(num_ngh, num_homes, run_time, log)
	world.make_world(season, weather, min_length, max_length, min_width, max_width, lower_t, upper_t)

	return flask.render_template('world.html', world_info = world)


@app.route('/world/step', methods=['GET'])
def step():
	global world
	
	num_steps = int(flask.request.form['num_steps'])
	
	for i in range(0, num_steps):
		world.step()
	
	return flask.render_template('world.html', world_info = world)

# get the data of the world at a step, if provided one. otherwise,
# proceed to the next step
@app.route('/st=<int:step_to>/get_data/<temp_scale>', methods=['GET'])
@app.route('/st=/get_data/<temp_scale>', methods=['GET'])
def get_step_data(step_to = None, temp_scale = 'celsius'):
	global world
	world_data = dict()

	# determine if the world needs to step forward
	if step_to is not None:
		step_to = int(step_to)
	else:
		world.step()
		step_to = world.world_clock.value

	if temp_scale == 'celsius':
		world_data['outside_temp'] = world.get_temp(step_to)
	else:
		world_data['outside_temp'] = c2f(world.get_temp(step_to))

	world_data['step'] = step_to

	for i in range(0, world.num_neighborhoods):
		world_data[i] = dict()
		
		for j in range(0, world.num_homes):
			home = world.neighborhoods[i].homes[j]
			
			if temp_scale == 'celsius':
				world_data[i][j] = {
						'temp': home.get_int_temp(step_to), 
						'color': home.color_gradient(step_to)
						}
			else:
				world_data[i][j] = {
						'temp': c2f(home.get_int_temp(step_to)), 
						'color': home.color_gradient(step_to)
						}

	return json.dumps(world_data)

# get information about a neighborhood, house, or device at a time step
@app.route('/st=<int:step_to>/<int:neighborhood_id>', methods=['GET'])
@app.route('/st=<int:step_to>/<int:neighborhood_id>/<int:house_id>', methods=['GET'])
@app.route('/st=<int:step_to>/<int:neighborhood_id>/<int:house_id>/<device>', methods=['GET'])
def get_info_data(step_to=None, neighborhood_id=None, house_id=None, device=None):
	global world
	info = dict()

	if neighborhood_id is not None:
		neighborhood_id = int(neighborhood_id)
		cur_n = world.neighborhoods[neighborhood_id]
		homes = list()
	
		if step_to is None:
			step_to = world.world_clock.value
		else:
			step_to = int(step_to)

		if house_id is None:
			homes = cur_n.homes	
		else:
			house_id = int(house_id)
			homes.append(cur_n.homes[house_id])

		if device is not None:
			if device == "thermostat":
				for home in homes:
					info[home.h_id] = {
							'start_temp': home.thermostat.start_temp,
							'start_time': home.thermostat.start_time,
							'end_time': home.thermostat.end_time,
							'mode': home.thermostat.mode
							}
				
			elif device == "battery":
				for home in homes:
					info[home.h_id] = {
							'max_capacity': home.battery.max_capacity,
							'current_capacity': home.battery.current_capacity,
							'amps': home.battery.amps,
							'voltage': home.battery.voltage
							}

			elif device == "pv":
				for home in homes:
					info[home.h_id] = {
							'num_cells': home.pv.num_cells,
							'watts': home.pv.wattage,
							'efficiency': home.pv.efficiency
							}
			else:
				for home in homes:
					info[home.h_id] = {
							'consumption': home.devices[device].consumption,
							'state': home.devices[device].state,
							'on_time': home.devices[device].on_time,
							'off_time': home.devices[device].off_time
							}

		else:
			for home in homes:
				info[home.h_id] = {
						'world_temp': cur_n.outside_temp.value,
						'neighborhood_id': home.n_id,
						'house_id': home.h_id,
						'num_floors': home.num_floors,

						'length': home.length,
						'width': home.width,
						'height': home.height,

						'target_temp': home.get_target_temp(),
						'internal_temp': home.get_int_temp(step_to),

						'wall_type': home.walls.type,
						'wall_thickness': home.walls.thickness,
						'wall_mass': home.walls.mass,
						'wall_R': home.walls.R,
						'wall_emissivity': home.walls.e
						}
	
	return json.dumps(info)


@app.route('/world/data')
@app.route('/world/data/<int:step>')
def get_world_data(step=None):
	global world
	info = dict()

	if step is None:
		info['clock'] = world.world_clock.value
		info['world_temp'] = world.outside_temp.value
	else:
		info['clock'] = int(step)
		info['world_temp'] = world.temp_history[int(step)]

	return json.dumps(info)

# interact with the devices in a house or a common device of all houses in
# a neighborhood
@app.route('/dev/<device>/<cmd>/<int:neighborhood_id>', methods=['GET'])
@app.route('/dev/<device>/<cmd>/<int:neighborhood_id>/<int:house_id>', methods=['GET'])
def device_api(device=None, cmd=None, neighborhood_id=None, house_id=None):
	global world
	
	if neighborhood_id is None or device is None or cmd is None:
		get_info_data()

	else:
		homes = list()
		neighborhood_id = int(neighborhood_id)

		cmd_list = cmd.split('_')

		if house_id is None:
			for home in world.neighborhoods[neighborhood_id].homes:
				homes.append(home)
		else:
			house_id = int(house_id)
			homes.append(world.neighborhoods[neighborhood_id].homes[house_id])

		if device == "thermostat":
			if any('target=' in s for s in cmd_list):
				for cmd_str in cmd_list:
					if 'target=' in cmd_str:
						target_temp = f2c(int(cmd_str.replace('target=', '')))

						for home in homes:
							home.thermostat.set_target_temp(target_temp)

			if 'heat' in cmd_list:
				for home in homes:
					home.thermostat.set_mode(2)

			elif 'cool' in cmd_list:
				for home in homes:
					home.thermostat.set_mode(1)

			if 'on' in cmd_list:
				for home in homes:
					home.thermostat.fan_on()
			
			elif 'off' in cmd_list:
				for home in homes:
					home.thermostat.fan_off()

		elif device == "evcs":
			if 'on' in cmd_list:
				for home in homes:
					home.devices["evcs"].turn_on()
			
			elif 'off' in cmd_list:
				for home in homes:
					home.devices["evcs"].turn_off()

		elif device == "pool_pump":
			if 'on' in cmd_list:
				for home in homes:
					home.devices["pool_pump"].turn_on()
			
			elif 'off' in cmd_list:
				for home in homes:
					home.devices["pool_pump"].turn_off()

	return flask.redirect(flask.url_for('get_info_data', step_to = world.world_clock.value,
										neighborhood_id = neighborhood_id, house_id = house_id,
										device = device))


if __name__ == '__main__':
	app.config["DEBUG"] = True
	app.run()
