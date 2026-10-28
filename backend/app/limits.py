from starlette.responses import JSONResponse


class UploadBodyLimit:
    """Bound multipart bodies before the framework spools files to disk."""

    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'] != '/api/documents':
            return await self.app(scope, receive, send)
        body, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > self.max_bytes:
                response = JSONResponse({'detail': '업로드 용량 제한을 초과했습니다.'}, status_code=413)
                return await response(scope, receive, send)
            body.append(message.get('body', b''))
            if not message.get('more_body', False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': b''.join(body), 'more_body': False}
            return await receive()

        await self.app(scope, replay, send)
