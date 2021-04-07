import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
bind = '127.0.0.1:8081'
umask = 0o007
reload = True

#logging
accesslog = '-'
errorlog = '-'