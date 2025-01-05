export async function getMacAddress(): Promise<string | null> {
  try {
    // 使用WebRTC获取本地IP地址
    const peerConnection = new RTCPeerConnection({ iceServers: [] })
    const dataChannel = peerConnection.createDataChannel('mac')
    
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        const candidate = event.candidate.candidate
        const matches = candidate.match(/[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}/)
        if (matches) {
          peerConnection.close()
          return matches[0]
        }
      }
    }

    const offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)
    
    // 等待1秒获取MAC地址
    return new Promise((resolve) => {
      setTimeout(() => {
        peerConnection.close()
        resolve(null)
      }, 1000)
    })
  } catch (error) {
    console.error('Failed to get MAC address:', error)
    return null
  }
}
