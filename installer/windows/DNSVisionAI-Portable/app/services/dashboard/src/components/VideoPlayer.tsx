'use client'

import { useEffect, useRef, useState } from 'react'

const GO2RTC_URL = process.env.NEXT_PUBLIC_GO2RTC_URL || 'http://localhost:1984'

interface VideoPlayerProps {
  cameraName: string
  className?: string
}

export function VideoPlayer({ cameraName, className }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [error, setError] = useState<string | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    let cleanup = false

    async function startWebRTC() {
      try {
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        })
        pcRef.current = pc

        pc.addTransceiver('video', { direction: 'recvonly' })
        pc.addTransceiver('audio', { direction: 'recvonly' })

        pc.ontrack = (event) => {
          if (video && event.streams[0]) {
            video.srcObject = event.streams[0]
          }
        }

        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        const response = await fetch(`${GO2RTC_URL}/api/webrtc?src=${encodeURIComponent(cameraName)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/sdp' },
          body: offer.sdp,
        })

        if (!response.ok) {
          throw new Error(`WebRTC negotiation failed: ${response.status}`)
        }

        const answer = await response.text()
        await pc.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: answer }))
      } catch (e: any) {
        if (!cleanup) {
          console.warn('WebRTC failed, falling back to HLS:', e.message)
          setError(e.message)
          // Fallback to HLS
          if (video) {
            const hlsUrl = `${GO2RTC_URL}/api/stream.m3u8?src=${encodeURIComponent(cameraName)}`
            try {
              const Hls = (await import('hls.js')).default
              if (Hls.isSupported()) {
                const hls = new Hls()
                hls.loadSource(hlsUrl)
                hls.attachMedia(video)
              } else {
                video.src = hlsUrl
              }
              setError(null)
            } catch {
              setError('Unable to connect to camera stream')
            }
          }
        }
      }
    }

    startWebRTC()

    return () => {
      cleanup = true
      pcRef.current?.close()
      if (video) video.srcObject = null
    }
  }, [cameraName])

  return (
    <div className={className}>
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 text-sm text-muted-foreground">
          {error}
        </div>
      )}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="h-full w-full object-cover"
      />
    </div>
  )
}
