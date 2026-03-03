class VisitLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"User: {request.user} visited: {request.path}")
        response = self.get_response(request)
        return response