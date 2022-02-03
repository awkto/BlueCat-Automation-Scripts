import base64
passfile = open(".password").read().splitlines()[0]
hash = base64.b64encode(passfile.encode("utf-8"))
print(hash)
