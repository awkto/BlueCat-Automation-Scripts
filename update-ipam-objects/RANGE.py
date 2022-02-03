import ipaddress

class RANGE():
    def __init__(self, start, end):
        self._start = ipaddress.ip_address(unicode(start))
        self._end = ipaddress.ip_address(unicode(end))

    def has(self, addr):
        tocheck = ipaddress.ip_address(unicode(addr))
        if int(tocheck) >= int(self._start) and int(tocheck) <= int(self._end):
            return True
        else:
            return False

    def conflicts(self, start, end):
        to_start = ipaddress.ip_address(unicode(start))
        to_end = ipaddress.ip_address(unicode(end))
        if int(to_start) <= int(self._start) and  int(to_end) >= int(self._start):
            return True
        if int(to_end) >= int(self._end) and int(to_start) <= int(self._end):
            return True
        return False
 
    def show(self):
        return str(self._start) + ' - ' + str(self._end)
