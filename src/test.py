import os

for filename in os.listdir("src/custom_actions"):
    if filename.endswith(".py") and filename != "__init__.py":
        print(filename)