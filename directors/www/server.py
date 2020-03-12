
def hello_world(environ, start_response):
    status = '200 OK'
    res = "Hello world!".encode('utf-8')
    response_headers = [
        ('Content-type','text/plain'),
        ('Content-Length',str(len(res)))
    ]
    start_response(status, response_headers)
    return iter([res])

