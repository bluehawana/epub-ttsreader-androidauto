-- MySQL schema for EPUB Audiobook Service
-- Run this after creating JawsDB MySQL addon

-- Users table for authentication and QR linking
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100),
    qr_token VARCHAR(100) UNIQUE,
    android_device_id VARCHAR(100),
    linked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audiobooks table
CREATE TABLE IF NOT EXISTS audiobooks (
    id VARCHAR(50) PRIMARY KEY,  -- UUID from processing job
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    chapters INT DEFAULT 0,
    total_duration INT DEFAULT 0,  -- seconds
    file_size BIGINT DEFAULT 0,  -- bytes
    status VARCHAR(20) DEFAULT 'processing',  -- processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Chapters table for individual MP3 files
CREATE TABLE IF NOT EXISTS chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audiobook_id VARCHAR(50) NOT NULL,
    chapter_number INT NOT NULL,
    title VARCHAR(500),
    url TEXT,  -- S3 URL
    duration INT DEFAULT 0,  -- seconds
    file_size BIGINT DEFAULT 0,  -- bytes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (audiobook_id) REFERENCES audiobooks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_chapter (audiobook_id, chapter_number),
    INDEX idx_audiobook_id (audiobook_id)
);

-- Processing jobs tracking
CREATE TABLE IF NOT EXISTS processing_jobs (
    job_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',  -- queued, processing, completed, failed
    progress INT DEFAULT 0,  -- percentage
    total_chapters INT DEFAULT 0,
    processed_chapters INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);