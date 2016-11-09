
#include "bmp_format.h"
#include "province_map.h"
#include "error.h"

#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstdlib>
#include <cassert>
#include <iostream>
#include <string>

province_map::province_map(const default_map& dm)
    : _p_map(nullptr),
      _n_width(0),
      _n_height(0) {

    color2id_map_t color2id_map;
    fill_color2id_map(color2id_map, dm);

	const std::string sp = fs::path(dm.root_path() / "map" / dm.provinces_path()).string();
    const char* path = sp.c_str();

    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    bmp_file_header bf_hdr;
    errno = 0;

    if ( fread(&bf_hdr, sizeof(bf_hdr), 1, f) < 1 ) {
        if (errno)
            throw va_error("failed to read bitmap file header: %s: %s", strerror(errno), path);
        else
            throw va_error("unexpected EOF: %s", path);
    }

    if (bf_hdr.magic != BMP_MAGIC)
        throw va_error("unsupported bitmap file type (magic=%04x): %s", bf_hdr.magic, path);

    assert( bf_hdr.n_header_size >= 40 );
    assert( bf_hdr.n_width > 0 );
    assert( bf_hdr.n_height > 0 ); // TODO (though not sure if game supports top-to-bottom scan order)
    assert( bf_hdr.n_planes == 1 );
    assert( bf_hdr.n_bpp == 24 );
    assert( bf_hdr.compression_type == 0 );
    assert( bf_hdr.n_colors == 0 );
    assert( bf_hdr.n_important_colors == 0 );

    _n_width = bf_hdr.n_width;
    _n_height = bf_hdr.n_height;

    /* calculate row size with 32-bit alignment padding */
    uint n_row_sz = 4 * ((bf_hdr.n_bpp * _n_width + 31) / 32);

    if (bf_hdr.n_bitmap_size)
        assert( bf_hdr.n_bitmap_size == n_row_sz * _n_height );

    /* allocate ID map */
    _p_map = new uint16_t[_n_width * _n_height];

    /* seek past any other bytes and directly to offset of pixel array (if needed). */
    if ( fseek(f, bf_hdr.n_bitmap_offset, SEEK_SET) != 0 )
        throw va_error("failed to seek to raw bitmap data (offset=%lu): %s: %s",
                       bf_hdr.n_bitmap_offset,
                       strerror(errno),
                       path);

    /* read bitmap image data (pixel array), row by row, in bottom-to-top raster scan order */

	uint8_t* p_row = new uint8_t[n_row_sz];

    for (uint row = 0; row < _n_height; ++row) {

        if ( fread(p_row, n_row_sz, 1, f) < 1 ) {
            if (errno)
                throw va_error("failed to read raw bitmap data: %s: %s", strerror(errno), path);
            else
                throw va_error("unexpected EOF while reading raw bitmap data: %s", path);
        }

        const uint y = _n_height-1 - row;

        /* cache previous pixel's value & province ID */
        uint8_t  prev_b;
        uint8_t  prev_g;
        uint8_t  prev_r;
        uint16_t prev_id;

        for (uint x = 0; x < _n_width; ++x) {
            const uint8_t* p = &p_row[3*x];
            uint16_t id;

            if (p[0] == 0xFF && p[1] == 0xFF && p[2] == 0xFF)
                id = TYPE_OCEAN;
            else if (p[0] == 0x00 && p[1] == 0x00 && p[2] == 0x00)
                id = TYPE_IMPASSABLE;
            else if (x > 0 && p[0] == prev_b && p[1] == prev_g && p[2] == prev_r)
                id = prev_id;
            else {

                uint32_t color = make_color(p[2], p[1], p[0]);
                auto i = color2id_map.find(color);

                if (i == color2id_map.end())
                    throw va_error("unexpected color RGB(%hhu, %hhu, %hhu) in provinces bitmap at (%u, %u)",
                                   p[2], p[1], p[0], x, y);

                id = i->second;
            }

            prev_b = p[0];
            prev_g = p[1];
            prev_r = p[2];
            prev_id = _p_map[y*_n_width + x] = id;
        }
    }

    fclose(f);
}


void province_map::fill_color2id_map(color2id_map_t& m, const default_map& dm) {

    const std::string sp = fs::path(dm.root_path() / "map" / dm.definitions_path()).string();
    const char* path = sp.c_str();
    FILE* f;

    if ( (f = fopen(path, "rb")) == nullptr )
        throw va_error("could not open file: %s: %s", strerror(errno), path);

    char buf[128];
    uint n_line = 0;

    if ( fgets(&buf[0], sizeof(buf), f) == nullptr ) // consume CSV header
        throw va_error("definitions file lacks at least 1 line of text: %s", path);

    while ( fgets(&buf[0], sizeof(buf), f) != nullptr ) {

        ++n_line;

        char* p = &buf[0];

        if (*p == '#')
            continue;

        char* n_str[4];
        n_str[0] = strtok(p, ";");

        for (uint x = 1; x < 4; ++x)
            n_str[x] = strtok(nullptr, ";");

        uint n[4];
        char* p_end;

        for (uint x = 0; x < 4; ++x) {
            n[x] = strtol(n_str[x], &p_end, 10);
            assert( *p_end == '\0' );
        }

        m.emplace( make_color(n[1], n[2], n[3]), static_cast<uint16_t>(n[0]) );

        if (n[0] == dm.max_province_id())
            break;
    }

    fclose(f);

    if (m.empty())
        throw va_error("definitions file lacked any data: %s", path);
}