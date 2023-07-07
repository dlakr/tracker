#!/bin/bash

# Get the frontmost application's process ID
pid=$(osascript -e 'tell application "System Events" to get the unix id of the frontmost process')

# Get the path of the frontmost application's executable
path=$(ps -p "$pid" -o comm=)

# Get the active file name
filename=$(osascript -e "tell application \"$path\" to get name of document 1")

echo "Active file name: $filename"