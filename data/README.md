# Data Directory

This directory contains data files, logs, and temporary files used by the system.

## Directory Structure

### `/temp/` - Temporary and Working Files
Temporary files created during system operation:
- `classification_progress.txt` - Progress tracking for classification tasks
- `progress.txt` - General progress tracking
- `user_ids.txt` - Temporary user ID data
- `TODO.txt` - Development notes and tasks

### `/logs/` - Log Files
System and application log files (currently empty, ready for future use)

## Usage

- **Temporary files** in `/temp/` can be safely deleted and will be regenerated as needed
- **Log files** in `/logs/` contain system operation information
- The main data storage is in the database (Qdrant + Supabase), not in these files

## Note

Most of these files are temporary and can be regenerated. They're kept for reference and debugging purposes. 