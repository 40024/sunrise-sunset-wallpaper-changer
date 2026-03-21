# What
Python script that dynamically changes wallpaper depending on dawn, day, dusk, night

# Why
I couldn't find anything that did this elegantly already on my linux environment

# What to adjust
Create service files like example files in this repo (suggested path ~/.config/systemd/user), and start with something like: 
    `systemctl --user daemon-reload`
    `systemctl --user enable dynamic-wallpaper.service`
WALLPAPERS mapping depending on what wallpapers you want

Latitude longitude in requests.get

swww calls if you're using a different wallpaper manager

# Collab
Feel free to submit a pr, I check my email so I will certainly see it
