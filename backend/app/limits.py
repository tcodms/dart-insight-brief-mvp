from fastapi import HTTPException
from starlette.formparsers import MultiPartException, MultiPartParser


async def parse_upload(request, max_bytes):
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'multipart/form-data':
        raise HTTPException(415, 'multipart/form-data 요청이 필요합니다.')

    async def limited_stream():
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > max_bytes:
                raise HTTPException(413, '업로드 용량 제한을 초과했습니다.')
            yield chunk

    length = request.headers.get('content-length', '')
    if length.isascii() and length.isdecimal():
        digits = length.lstrip('0') or '0'
        if len(digits) > len(str(max_bytes)) or int(digits) > max_bytes:
            raise HTTPException(413, '업로드 용량 제한을 초과했습니다.')
    try:
        return await MultiPartParser(request.headers, limited_stream(), max_files=1, max_fields=1).parse()
    except MultiPartException as error:
        raise HTTPException(400, '업로드 형식이 올바르지 않습니다.') from error
