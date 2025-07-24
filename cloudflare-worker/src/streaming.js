/**
 * Audio streaming utilities for CF Worker
 */

export async function handleAudioStream(request, env, corsHeaders) {
  try {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Extract R2 key from path: /api/stream/userId/jobId/chapter_1.mp3
    const pathParts = path.split('/').slice(3); // Remove /api/stream
    const r2Key = pathParts.join('/');
    
    if (!r2Key) {
      return new Response('Invalid stream path', { 
        status: 400, 
        headers: corsHeaders 
      });
    }

    // Get audio file from R2
    const audioObject = await env.EPUB_BUCKET.get(r2Key);
    
    if (!audioObject) {
      return new Response('Audio file not found', { 
        status: 404, 
        headers: corsHeaders 
      });
    }

    // Handle range requests for audio streaming
    const range = request.headers.get('Range');
    const audioBuffer = await audioObject.arrayBuffer();
    const audioSize = audioBuffer.byteLength;

    if (range) {
      return handleRangeRequest(range, audioBuffer, audioSize, corsHeaders);
    }

    // Return full audio file
    return new Response(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioSize.toString(),
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=31536000', // 1 year cache
        ...corsHeaders
      }
    });

  } catch (error) {
    console.error('Audio streaming error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
}

function handleRangeRequest(rangeHeader, audioBuffer, totalSize, corsHeaders) {
  try {
    // Parse range header: "bytes=start-end"
    const rangeParts = rangeHeader.replace(/bytes=/, '').split('-');
    const start = parseInt(rangeParts[0], 10) || 0;
    const end = parseInt(rangeParts[1], 10) || totalSize - 1;
    
    // Validate range
    if (start >= totalSize || end >= totalSize || start > end) {
      return new Response('Range Not Satisfiable', {
        status: 416,
        headers: {
          'Content-Range': `bytes */${totalSize}`,
          ...corsHeaders
        }
      });
    }

    // Extract requested chunk
    const chunkSize = end - start + 1;
    const audioChunk = audioBuffer.slice(start, end + 1);

    return new Response(audioChunk, {
      status: 206, // Partial Content
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': chunkSize.toString(),
        'Content-Range': `bytes ${start}-${end}/${totalSize}`,
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=31536000',
        ...corsHeaders
      }
    });

  } catch (error) {
    console.error('Range request error:', error);
    return new Response('Internal Server Error', {
      status: 500,
      headers: corsHeaders
    });
  }
}