
export function convertGDriveUrl(url) {
  if (!url) return null;
  if (!url.includes('drive.google.com')) return url;

  try {
    let fileId = null;

    if (url.includes('/file/d/')) {
      fileId = url.split('/file/d/')[1].split('/')[0];
    } else if (url.includes('id=')) {
      fileId = url.split('id=')[1].split('&')[0];
    }

    // Thử nhiều format khác nhau của Google Drive
    if (fileId) {
      // Format 1: Direct download (thường work tốt nhất cho img tag)
      return `https://drive.google.com/uc?export=view&id=${fileId}`;
      
      // Backup formats nếu format trên không work:
      // return `https://lh3.googleusercontent.com/d/${fileId}`;
      // return `https://drive.google.com/thumbnail?id=${fileId}&sz=w1000`;
    }
    
    return url;
  } catch {
    return url;
  }
}
