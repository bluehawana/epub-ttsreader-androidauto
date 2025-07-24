/**
 * Durable Object for handling long-running TTS processing
 * Overcomes CF Worker CPU time limits for complex operations
 */

export class TTSProcessor {
  constructor(controller, env) {
    this.controller = controller;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    switch (path) {
      case '/process':
        return this.handleProcessRequest(request);
      case '/status':
        return this.handleStatusRequest(request);
      default:
        return new Response('Not Found', { status: 404 });
    }
  }

  async handleProcessRequest(request) {
    try {
      const data = await request.json();
      const { jobId, userId, bookTitle, chapters } = data;

      // Store job status
      await this.controller.storage.put(`job:${jobId}`, {
        status: 'processing',
        progress: 0,
        totalChapters: chapters.length,
        startTime: Date.now()
      });

      // Process chapters in batches to avoid timeout
      const batchSize = 2;
      const processedChapters = [];

      for (let i = 0; i < chapters.length; i += batchSize) {
        const batch = chapters.slice(i, i + batchSize);
        
        for (const [batchIndex, chapter] of batch.entries()) {
          const chapterIndex = i + batchIndex;
          
          try {
            // Convert chapter to speech
            const audioBuffer = await this.convertChapterToSpeech(chapter.text);
            
            if (audioBuffer) {
              // Upload to R2
              const r2Key = `${userId}/${jobId}/chapter_${chapterIndex + 1}.mp3`;
              await this.env.EPUB_BUCKET.put(r2Key, audioBuffer, {
                httpMetadata: { contentType: 'audio/mpeg' }
              });

              processedChapters.push({
                chapter: chapterIndex + 1,
                title: chapter.title,
                r2_key: r2Key,
                url: `/api/stream/${r2Key}`,
                duration: this.estimateAudioDuration(chapter.text)
              });

              // Update progress
              const progress = ((chapterIndex + 1) / chapters.length) * 100;
              await this.controller.storage.put(`job:${jobId}`, {
                status: 'processing',
                progress: Math.round(progress),
                totalChapters: chapters.length,
                completedChapters: chapterIndex + 1,
                startTime: Date.now()
              });
            }
          } catch (error) {
            console.error(`Failed to process chapter ${chapterIndex + 1}:`, error);
          }
        }

        // Small delay between batches to prevent resource exhaustion
        await this.sleep(100);
      }

      // Save final metadata
      const metadata = {
        job_id: jobId,
        user_id: userId,
        book_title: bookTitle,
        chapters: processedChapters,
        created_at: new Date().toISOString(),
        status: 'completed'
      };

      const metadataKey = `${userId}/${jobId}/metadata.json`;
      await this.env.EPUB_BUCKET.put(metadataKey, JSON.stringify(metadata), {
        httpMetadata: { contentType: 'application/json' }
      });

      // Update job status
      await this.controller.storage.put(`job:${jobId}`, {
        status: 'completed',
        progress: 100,
        totalChapters: chapters.length,
        completedChapters: processedChapters.length,
        completedAt: Date.now()
      });

      return new Response(JSON.stringify({ 
        success: true, 
        processedChapters: processedChapters.length 
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      console.error('TTS processing error:', error);
      
      // Update job status with error
      const { jobId } = await request.json();
      await this.controller.storage.put(`job:${jobId}`, {
        status: 'failed',
        error: error.message,
        failedAt: Date.now()
      });

      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  async handleStatusRequest(request) {
    try {
      const url = new URL(request.url);
      const jobId = url.searchParams.get('jobId');
      
      if (!jobId) {
        return new Response(JSON.stringify({ error: 'Job ID required' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      const jobStatus = await this.controller.storage.get(`job:${jobId}`);
      
      if (!jobStatus) {
        return new Response(JSON.stringify({ error: 'Job not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      return new Response(JSON.stringify(jobStatus), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  async convertChapterToSpeech(text, voice = 'en-US-AriaNeural') {
    // This is where we'd implement actual Edge TTS
    // For CF Workers, we might need to:
    // 1. Use a TTS API service
    // 2. Stream the conversion
    // 3. Use Web Speech API (if available)
    
    try {
      // Simulate TTS processing time
      await this.sleep(500 + Math.random() * 1000);
      
      // Mock MP3 generation
      // In reality, this would call Edge TTS or similar service
      const textLength = text.length;
      const estimatedAudioSize = Math.max(1024, textLength * 0.5); // Rough estimate
      
      // Generate mock MP3 data
      const mockMp3 = new Uint8Array(estimatedAudioSize);
      
      // Add MP3 header
      mockMp3[0] = 0xFF;
      mockMp3[1] = 0xFB;
      mockMp3[2] = 0x90;
      mockMp3[3] = 0x00;
      
      // Fill with pseudo-random data to simulate audio
      for (let i = 4; i < mockMp3.length; i++) {
        mockMp3[i] = Math.floor(Math.random() * 256);
      }

      console.log(`Generated ${mockMp3.length} bytes of audio for ${textLength} characters of text`);
      return mockMp3;

    } catch (error) {
      console.error('TTS conversion error:', error);
      throw error;
    }
  }

  estimateAudioDuration(text) {
    // Estimate based on reading speed: ~150 words per minute
    const wordsPerMinute = 150;
    const charactersPerWord = 5;
    const estimatedWords = text.length / charactersPerWord;
    const estimatedMinutes = estimatedWords / wordsPerMinute;
    return Math.round(estimatedMinutes * 60); // Return seconds
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}