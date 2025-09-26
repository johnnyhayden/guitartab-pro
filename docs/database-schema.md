# Database Schema Design

## Overview

This document outlines the PostgreSQL database schema for GuitarTab Pro, a guitar TAB and lyrics/chord organizer application.

## Requirements

### Core Entities

1. **Users**: User accounts with authentication and preferences
2. **Songs**: Individual songs with metadata, chords, and lyrics
3. **Songlists**: Collections of songs organized by users
4. **Songlist_Songs**: Many-to-many relationship between songlists and songs
5. **User_Preferences**: User-specific display and behavior settings

### Functional Requirements

- **User Management**: Secure user registration, login, and profile management
- **Song Storage**: Store song metadata, chord progressions, and lyrics
- **Songlist Organization**: Users can create and manage multiple songlists
- **Search Capabilities**: Full-text search on songs by title, artist, lyrics
- **Preferences**: User-customizable display settings and behavior
- **Performance**: Efficient queries for large song libraries

## Entity Relationship Diagram (ERD)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users       │    │     Songs       │    │   Songlists     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ user_id (PK)    │    │ song_id (PK)    │    │ songlist_id (PK)│
│ username        │    │ title           │    │ name            │
│ email           │    │ artist          │    │ description     │
│ password_hash   │    │ genre           │    │ user_id (FK)    │
│ created_at      │    │ key             │    │ created_at      │
│ last_login      │    │ tempo           │    │ updated_at      │
└─────────────────┘    │ difficulty      │    │ is_public       │
                       │ capo_position   │    └─────────────────┘
                       │ chord_progression│           │
                       │ lyrics          │           │
                       │ source          │           │
                       │ source_id       │           │
                       │ created_by (FK) │           │
                       │ created_at      │           │
                       └─────────────────┘           │
                              │                      │
                              │                      │
                       ┌─────────────────┐           │
                       │ Songlist_Songs  │◄──────────┘
                       ├─────────────────┤
                       │ songlist_id (FK)│
                       │ song_id (FK)    │
                       │ position        │
                       │ notes           │
                       │ added_at        │
                       └─────────────────┘

┌─────────────────┐
│ User_Preferences│
├─────────────────┤
│ user_id (PK)    │
│ chord_color     │
│ lyric_color     │
│ background_color│
│ title_color     │
│ font_size       │
│ auto_scroll_speed│
│ metronome_settings│
│ display_mode    │
└─────────────────┘
```

## Naming Conventions

### Tables
- Use snake_case
- Plural nouns
- Examples: `users`, `songs`, `songlists`, `songlist_songs`, `user_preferences`

### Columns
- Use snake_case
- Descriptive names
- Foreign keys: `{table_name}_id`
- Timestamps: `created_at`, `updated_at`, `last_login`
- Boolean flags: `is_public`, `is_active`

### Indexes
- Primary keys: `pk_{table_name}`
- Foreign keys: `fk_{table_name}_{column_name}`
- Unique constraints: `uk_{table_name}_{column_name}`
- Search indexes: `idx_{table_name}_{column_name}`

### Constraints
- Primary keys: `pk_{table_name}`
- Foreign keys: `fk_{table_name}_{column_name}`
- Unique constraints: `uk_{table_name}_{column_name}`
- Check constraints: `ck_{table_name}_{column_name}`

## Data Types

### Common Types
- **IDs**: `SERIAL PRIMARY KEY` or `BIGSERIAL PRIMARY KEY`
- **Text**: `VARCHAR(n)` for limited text, `TEXT` for unlimited
- **Timestamps**: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- **Booleans**: `BOOLEAN DEFAULT FALSE`
- **JSON**: `JSONB` for structured data (preferences, metadata)

### Specific Fields
- **Email**: `VARCHAR(255) UNIQUE NOT NULL`
- **Password Hash**: `VARCHAR(255) NOT NULL`
- **Song Title**: `VARCHAR(500) NOT NULL`
- **Artist**: `VARCHAR(255) NOT NULL`
- **Lyrics**: `TEXT`
- **Chord Progression**: `TEXT` (formatted as JSON or custom format)
- **Colors**: `VARCHAR(7)` (hex color codes)

## Relationships

### One-to-Many
- Users → Songs (created_by)
- Users → Songlists (user_id)
- Users → User_Preferences (user_id)

### Many-to-Many
- Songs ↔ Songlists (via Songlist_Songs)

### Constraints
- Cascade deletes for user-related data
- Restrict deletes for song references
- Unique constraints on email, username
- Check constraints for valid data ranges

## Performance Considerations

### Indexes
- Primary keys (automatic)
- Foreign key columns
- Search columns (title, artist, lyrics)
- Composite indexes for common queries
- Full-text search indexes

### Query Optimization
- Use appropriate data types
- Normalize data structure
- Consider denormalization for read-heavy operations
- Implement proper indexing strategy

## Security Considerations

- Password hashing (bcrypt)
- Input validation
- SQL injection prevention
- Access control at application level
- Audit logging for sensitive operations
