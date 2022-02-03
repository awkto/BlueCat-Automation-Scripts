import base64
secretfile = open(".secret").read().splitlines()[0]
passw = base64.b64decode(secretfile.decode("utf-8"))
print(passw)
