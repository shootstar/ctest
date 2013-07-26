import logging
import inspect

logger = logging.getLogger("ceilometer-test")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(module)s:%(filename)s:%(funcName)s:%(lineno)d %(message)s","%H:%M:%S")
fh = logging.FileHandler("/tmp/ceilometer.log")
fh.setFormatter(formatter)

logger.addHandler(fh)

def get_caller(num=5):
    current_frame = inspect.currentframe()
    outerframes = inspect.getouterframes(current_frame)
    return map(lambda x:[x[1],x[2],x[3]],outerframes)[1:num]

#def get_caller(num=5):
#    record = dict()
#    current_frame = None
#    for x in xrange(num):
#        if current_frame is None:
#           current_frame = inspect.currentframe()
#        current_frame = getattr(current_frame,"f_back")
#        caller = inspect.getframeinfo(curent_frame)[2]
#        record[caller] = record.get(caller,0) + 1
#    callers = sorted(record.items(),key=lambda a:a[1])
#    return callers

