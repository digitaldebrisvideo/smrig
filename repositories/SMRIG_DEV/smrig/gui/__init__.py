import os

# add to mayas icon path
icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons"))
os.environ["XBMLANGPATH"] = "{}{}{}".format(icon_path, os.pathsep, os.environ.get("XBMLANGPATH", ""))
