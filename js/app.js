import * as mediasoupClient from 'mediasoup-client';

document.addEventListener('DOMContentLoaded', () => {
    startStreaming();
});

async function startStreaming() {
    const localVideo = document.getElementById('localVideo');

    if (!localVideo) {
        console.error('Video element not found');
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        localVideo.srcObject = stream;

        const device = new mediasoupClient.Device();
        const routerRtpCapabilities = await fetch('/getRouterRtpCapabilities').then(response => response.json());
        await device.load({ routerRtpCapabilities });

        const transportParams = await fetch('/createTransport').then(response => response.json());
        const sendTransport = device.createSendTransport(transportParams);

        sendTransport.on('connect', async ({ dtlsParameters }, callback, errback) => {
            try {
                await fetch('/connectTransport', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dtlsParameters })
                });
                callback();
            } catch (error) {
                errback(error);
            }
        });

        sendTransport.on('produce', async ({ kind, rtpParameters }, callback, errback) => {
            try {
                const { id } = await fetch('/produce', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ kind, rtpParameters })
                }).then(response => response.json());
                callback({ id });
            } catch (error) {
                errback(error);
            }
        });

        const videoTrack = stream.getVideoTracks()[0];
        await sendTransport.produce({ track: videoTrack });
    } catch (error) {
        console.error('Error during startStreaming:', error);
    }
}