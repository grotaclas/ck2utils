
#ifndef _MDH_PROVINCE_MAP_H_
#define _MDH_PROVINCE_MAP_H_

#include "mod_vfs.h"
#include "default_map.h"
#include "definitions_table.h"
#include "color.h"

#include <cstdint>


class province_map {
    uint16_t* _p_map;
    uint _n_width;
    uint _n_height;

public:
    province_map(const mod_vfs&, const default_map&, const definitions_table&);
    ~province_map() { delete[] _p_map; }

    static const uint16_t TYPE_OCEAN = UINT16_MAX;
    static const uint16_t TYPE_IMPASSABLE = UINT16_MAX-1;
    static const uint16_t REAL_ID_MAX = UINT16_MAX-2;

    uint      width() const noexcept  { return _n_width; }
    uint      height() const noexcept { return _n_height; }
    const uint16_t* map() const noexcept { return _p_map; }
    uint16_t* map() noexcept { return _p_map; }

    uint16_t at(uint x, uint y) const noexcept { return _p_map[ y*_n_width + x ]; }
};


#endif
