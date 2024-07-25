import secrets
from aiohttp import web
import aiohttp_cors
from pymediasoup import AiortcHandler, Device, transport
import os

# Установите путь к вашей директории с проектом
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


async def handle_offer(request):
    try:
        params = await request.json()
        offer = params.get('offer', {})

        router_rtp_capabilities = offer.get('routerRtpCapabilities')
        ice_parameters = offer.get('iceParameters')
        ice_candidates = offer.get('iceCandidates')
        dtls_parameters = offer.get('dtlsParameters')
        sctp_parameters = offer.get('sctpParameters')
        rtp_parameters = offer.get('rtpParameters')

        if not all([router_rtp_capabilities, ice_parameters, ice_candidates, dtls_parameters, sctp_parameters,
                    rtp_parameters]):
            raise ValueError("Missing one or more required fields in the offer")

        device = Device(handlerFactory=AiortcHandler.createFactory())
        await device.load({"routerRtpCapabilities": router_rtp_capabilities})

        send_transport = await device.createSendTransport(
            id=secrets.token_hex(8),
            iceParameters=ice_parameters,
            iceCandidates=ice_candidates,
            dtlsParameters=dtls_parameters,
            sctpParameters=sctp_parameters
        )

        await send_transport.connect(dtlsParameters=dtls_parameters)

        consumer = await send_transport.consume(
            id=secrets.token_hex(8),
            producerId=secrets.token_hex(8),
            kind='video',
            rtpParameters=rtp_parameters
        )

        response = {
            "id": send_transport.id,
            "rtpCapabilities": device.rtpCapabilities,
            "consumer": {
                "id": consumer.id,
                "kind": consumer.kind,
                "rtpParameters": consumer.rtpParameters,
                "producerId": consumer.producerId
            }
        }

        return web.json_response(response)

    except Exception as e:
        print(f"Error handling request: {e}")
        return web.json_response({"error": str(e)}, status=400)


async def get_router_rtp_capabilities(request):
    try:
        device = Device(handlerFactory=AiortcHandler.createFactory())
        await device.load({"routerRtpCapabilities": {}})
        return web.json_response(device.rtpCapabilities.dict())
    except Exception as e:
        print(f"Error handling request: {e}")
        return web.json_response({"error": str(e)}, status=400)


async def get_ice_parameters(request):
    return web.json_response(transport.iceParameters)


async def get_ice_candidates(request):
    return web.json_response(transport.iceCandidates)


async def get_dtls_parameters(request):
    return web.json_response(transport.dtlsParameters)


async def create_transport(request):
    try:
        transport_params = await request.json()
        # Ваш код для создания транспорта
        return web.json_response(transport_params)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)


async def connect_transport(request):
    try:
        params = await request.json()
        await transport.connect(params['dtlsParameters'])
        return web.json_response({'status': 'connected'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)


async def produce(request):
    try:
        params = await request.json()
        producer = await transport.produce(kind=params['kind'], rtpParameters=params['rtpParameters'])
        return web.json_response({'id': producer.id})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)


app = web.Application()

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*",
    )
})

app.router.add_post('/offer', handle_offer)
app.router.add_get('/getRouterRtpCapabilities', get_router_rtp_capabilities)
app.router.add_get('/getIceParameters', get_ice_parameters)
app.router.add_get('/getIceCandidates', get_ice_candidates)
app.router.add_get('/getDtlsParameters', get_dtls_parameters)
app.router.add_post('/createTransport', create_transport)
app.router.add_post('/connectTransport', connect_transport)
app.router.add_post('/produce', produce)

# Настройка маршрутов для статических файлов
app.router.add_static('/js/', path=os.path.join(PROJECT_DIR, 'js'), name='js')
app.router.add_static('/static/', path=os.path.join(PROJECT_DIR, 'static'), name='static')

for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    web.run_app(app, port=8000)
