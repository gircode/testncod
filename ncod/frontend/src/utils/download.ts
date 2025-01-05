export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function downloadFile(url: string, filename: string) {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    downloadBlob(blob, filename)
  } catch (error) {
    console.error('Download failed:', error)
    throw error
  }
} 