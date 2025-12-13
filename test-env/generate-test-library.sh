#!/bin/bash
# Generate a ~2GB test audiobook library with varied structures
# Tests different folder patterns, authors, series, edge cases

TEST_LIB="${1:-/home/deucebucket/library-manager/test-env/test-audiobooks}"
TARGET_SIZE_MB=2048  # 2GB
CREATED_MB=0

# Create base directory
rm -rf "$TEST_LIB"
mkdir -p "$TEST_LIB"

echo "Generating ~2GB test library at: $TEST_LIB"

# Function to create a dummy MP3 file of specified size (MB)
create_audio_file() {
    local path="$1"
    local size_mb="${2:-10}"
    mkdir -p "$(dirname "$path")"
    dd if=/dev/urandom of="$path" bs=1M count=$size_mb status=none 2>/dev/null
    CREATED_MB=$((CREATED_MB + size_mb))
}

# ==========================================
# STANDARD STRUCTURES (Author/Title)
# ==========================================
echo "Creating standard Author/Title structures..."

create_audio_file "$TEST_LIB/Stephen King/The Shining/01 - Chapter 1.mp3" 15
create_audio_file "$TEST_LIB/Stephen King/The Shining/02 - Chapter 2.mp3" 15
create_audio_file "$TEST_LIB/Stephen King/It/Part 1.mp3" 20
create_audio_file "$TEST_LIB/Stephen King/It/Part 2.mp3" 20

create_audio_file "$TEST_LIB/George Orwell/1984/audiobook.mp3" 25
create_audio_file "$TEST_LIB/George Orwell/Animal Farm/full.mp3" 15

create_audio_file "$TEST_LIB/Jane Austen/Pride and Prejudice/chapter_01.mp3" 10
create_audio_file "$TEST_LIB/Jane Austen/Pride and Prejudice/chapter_02.mp3" 10
create_audio_file "$TEST_LIB/Jane Austen/Pride and Prejudice/chapter_03.mp3" 10

# ==========================================
# SERIES STRUCTURES (Author/Series/Title)
# ==========================================
echo "Creating Author/Series/Title structures..."

create_audio_file "$TEST_LIB/Brandon Sanderson/Mistborn/The Final Empire/01.mp3" 20
create_audio_file "$TEST_LIB/Brandon Sanderson/Mistborn/The Final Empire/02.mp3" 20
create_audio_file "$TEST_LIB/Brandon Sanderson/Mistborn/The Well of Ascension/audiobook.mp3" 30
create_audio_file "$TEST_LIB/Brandon Sanderson/Mistborn/The Hero of Ages/full.mp3" 30

create_audio_file "$TEST_LIB/J.K. Rowling/Harry Potter/Philosophers Stone/chapter1.mp3" 15
create_audio_file "$TEST_LIB/J.K. Rowling/Harry Potter/Philosophers Stone/chapter2.mp3" 15
create_audio_file "$TEST_LIB/J.K. Rowling/Harry Potter/Chamber of Secrets/part1.mp3" 20
create_audio_file "$TEST_LIB/J.K. Rowling/Harry Potter/Chamber of Secrets/part2.mp3" 20

create_audio_file "$TEST_LIB/Frank Herbert/Dune/Dune/01-intro.mp3" 25
create_audio_file "$TEST_LIB/Frank Herbert/Dune/Dune Messiah/audiobook.mp3" 20

# ==========================================
# DEEP NESTED WITH DISC FOLDERS
# ==========================================
echo "Creating deep nested structures with disc folders..."

create_audio_file "$TEST_LIB/Stephen King/Dark Tower/The Gunslinger/Disc 1/track01.mp3" 15
create_audio_file "$TEST_LIB/Stephen King/Dark Tower/The Gunslinger/Disc 1/track02.mp3" 15
create_audio_file "$TEST_LIB/Stephen King/Dark Tower/The Gunslinger/Disc 2/track01.mp3" 15
create_audio_file "$TEST_LIB/Stephen King/Dark Tower/The Gunslinger/Disc 2/track02.mp3" 15

create_audio_file "$TEST_LIB/Robert Jordan/Wheel of Time/The Eye of the World/CD1/01.mp3" 20
create_audio_file "$TEST_LIB/Robert Jordan/Wheel of Time/The Eye of the World/CD1/02.mp3" 20
create_audio_file "$TEST_LIB/Robert Jordan/Wheel of Time/The Eye of the World/CD2/01.mp3" 20

# ==========================================
# NUMBERED SERIES (01 - Title format)
# ==========================================
echo "Creating numbered series formats..."

create_audio_file "$TEST_LIB/Isaac Asimov/Foundation/01 - Foundation/book.mp3" 25
create_audio_file "$TEST_LIB/Isaac Asimov/Foundation/02 - Foundation and Empire/book.mp3" 25
create_audio_file "$TEST_LIB/Isaac Asimov/Foundation/03 - Second Foundation/book.mp3" 25

# ==========================================
# EDGE CASES - REVERSED STRUCTURES
# ==========================================
echo "Creating edge cases (reversed, problematic)..."

# Title as folder, Author as subfolder (WRONG)
create_audio_file "$TEST_LIB/Metro 2033/Dmitry Glukhovsky/audiobook.mp3" 20

# Series as root, no author
create_audio_file "$TEST_LIB/The Expanse/Leviathan Wakes/full.mp3" 30
create_audio_file "$TEST_LIB/The Expanse/Calibans War/full.mp3" 30

# Just title folder at root
create_audio_file "$TEST_LIB/The Hitchhikers Guide to the Galaxy/part1.mp3" 15
create_audio_file "$TEST_LIB/The Hitchhikers Guide to the Galaxy/part2.mp3" 15

# ==========================================
# VARIOUS NAMING CONVENTIONS
# ==========================================
echo "Creating various naming conventions..."

# Author - Title format in folder name
create_audio_file "$TEST_LIB/Neil Gaiman - American Gods/chapter01.mp3" 20
create_audio_file "$TEST_LIB/Neil Gaiman - American Gods/chapter02.mp3" 20

# Title (Year) format
create_audio_file "$TEST_LIB/Terry Pratchett/Good Omens (1990)/audiobook.mp3" 25

# Initials author
create_audio_file "$TEST_LIB/J.R.R. Tolkien/The Hobbit/chapter1.mp3" 20
create_audio_file "$TEST_LIB/J.R.R. Tolkien/The Hobbit/chapter2.mp3" 20
create_audio_file "$TEST_LIB/J.R.R. Tolkien/Lord of the Rings/Fellowship/disc1.mp3" 30

# ==========================================
# VARIOUS FILE TYPES AND EDGE CASES
# ==========================================
echo "Creating edge cases - multiple narrators, editions..."

create_audio_file "$TEST_LIB/Andy Weir/The Martian {RC Bray}/audiobook.mp3" 25
create_audio_file "$TEST_LIB/Andy Weir/The Martian {Wil Wheaton}/audiobook.mp3" 25
create_audio_file "$TEST_LIB/Andy Weir/Project Hail Mary/full.mp3" 30

# Different audio formats (still .mp3 extension for testing, but different names)
create_audio_file "$TEST_LIB/Agatha Christie/Murder on the Orient Express/audiobook.m4b" 20
create_audio_file "$TEST_LIB/Agatha Christie/And Then There Were None/book.m4a" 18

# ==========================================
# FILL TO ~2GB
# ==========================================
echo "Filling remaining space to reach ~2GB..."

# Add more books to reach target size
authors=("Michael Crichton" "Dan Brown" "Lee Child" "James Patterson" "John Grisham"
         "Tom Clancy" "Dean Koontz" "Clive Cussler" "Ken Follett" "David Baldacci")
books=("Thriller Book" "Mystery Novel" "Adventure Story" "Crime Fiction" "Suspense Tale")

count=1
while [ $CREATED_MB -lt $TARGET_SIZE_MB ]; do
    author="${authors[$((count % ${#authors[@]}))]}"
    book="${books[$((count % ${#books[@]}))]}"
    size=$((15 + RANDOM % 20))  # Random size between 15-35MB

    if [ $((CREATED_MB + size)) -gt $TARGET_SIZE_MB ]; then
        size=$((TARGET_SIZE_MB - CREATED_MB))
        [ $size -le 0 ] && break
    fi

    create_audio_file "$TEST_LIB/$author/$book $count/audiobook.mp3" $size
    count=$((count + 1))
done

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo "============================================"
echo "Test Library Generation Complete!"
echo "============================================"
echo "Location: $TEST_LIB"
echo "Size: $(du -sh "$TEST_LIB" | cut -f1)"
echo "Files: $(find "$TEST_LIB" -type f | wc -l)"
echo "Folders: $(find "$TEST_LIB" -type d | wc -l)"
echo ""
echo "Structure includes:"
echo "  - Standard Author/Title folders"
echo "  - Author/Series/Title with series detection"
echo "  - Deep nested with disc/CD folders"
echo "  - Numbered series (01 - Title format)"
echo "  - Edge cases (reversed, missing author)"
echo "  - Various naming conventions"
echo "  - Multiple narrator editions"
echo "============================================"
