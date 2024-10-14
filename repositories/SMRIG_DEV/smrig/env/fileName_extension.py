import glob
import json
import os
import subprocess
import csv
from PyQt5 import QtWidgets, QtCore


# Assuming necessary imports are done, including imports for maya's cmds and mel modules

def set_folder_externally(folder_path, button1, numEnt):
	def setFramerate(folder_path):

		json_files = glob.glob(folder_path + "/*.json")
		if len(json_files) == 1:
			json_file = json_files
		else:
			print("Warning: No json file, or multiple json files in folder")

		def timecode_to_frames(timecode, framerate):
			return sum(f * int(float(t)) for f, t in
			           zip((3600 * framerate, 60 * framerate, framerate, 1), timecode.split(':')))

		f = open(json_file[0])
		data = json.load(f)
		s_tc = data["startTimecode"]
		e_tc = data["endTimecode"]
		frames = data["frames"]

		r_tc30 = timecode_to_frames(e_tc, 30) - timecode_to_frames(s_tc, 30)
		r_tc60 = timecode_to_frames(e_tc, 60) - timecode_to_frames(s_tc, 60)

		stc_etc = [r_tc30, r_tc60]
		xxx = min(stc_etc, key=lambda x: abs(x - frames))
		if xxx == r_tc30:
			fps_string = "30fps"
			cmds.currentUnit(t=fps_string)
			print("Setting framerate to 30fps")
		else:
			fps_string = "60fps"
			cmds.currentUnit(t=fps_string)
			print("Setting framerate to 60fps")
		return frames, xxx, r_tc30

	no_frames, xxx, r_tc30 = setFramerate(folder_path)

	button1.setText(folder_path)

	csv_file = glob.glob(folder_path + "/*_cal.csv")

	qt_files = glob.glob(folder_path + "/*.mov")
	if len(qt_files) == 1:
		qt_file = qt_files[0]
	else:
		print("Warning: No mov file")

	script_path = __file__  # assuming the script_path is __file__

	folderpath, fileName = os.path.split(script_path)
	ffprobePath = os.path.join(folderpath, "ffprobe.exe")
	ffprobeCommand = f'{ffprobePath} -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "{qt_file}"'
	getd = subprocess.check_output(
		[ffprobePath, '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries',
		 'stream=nb_read_frames', '-print_format', 'csv', qt_file])

	try:
		getd = getd.decode('utf-8')
	except:
		pass

	duration_frames = int(getd.split(",")[1])
	print("no_frames:  ", no_frames)
	print("number of frames:  ", duration_frames)
	if xxx == r_tc30:
		numEnt.setValue(((no_frames * 2) - duration_frames) + 1)
		print("option1  ", ((no_frames * 2) - duration_frames) + 1)
	else:
		numEnt.setValue((duration_frames - no_frames) + 1)
		print("option2  ", (duration_frames - no_frames) + 1)

	csvNames, csvValues = "", []
	with open(csv_file[0], 'r') as csvfile:
		csv_reader = csv.reader(csvfile, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				csvNames = row
				line_count += 1
			else:
				csvValues.append(row)
				line_count += 1
	return csvNames, csvValues, qt_file

# Example of how it can be called
# folder_path = "path/to/your/folder"
# my_button1 = QtWidgets.QPushButton("Select folder...")
# my_numEnt = QtWidgets.QSpinBox()
# set_folder_externally(folder_path, my_button1, my_numEnt)
