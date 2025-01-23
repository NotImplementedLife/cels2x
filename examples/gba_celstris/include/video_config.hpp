#pragma once

#include <gba.h>

#include "memory.hpp"

inline static constexpr unsigned short _palette[] = {
	RGB8(0x00,0x00,0x00), RGB8(0x40,0x80,0xc0), RGB8(0xFF,0xFF,0xFF), 
	RGB8(0xF5,0xFF,0xFF), RGB8(0xDF,0xFF,0xF2),	RGB8(0xCA,0xFF,0xE2),
	RGB8(0xB7,0xFD,0xD8), RGB8(0x2C,0x4F,0x8B),
};

inline unsigned short* gfx_ptr = (unsigned short*)MAP_BASE_ADR(0);
inline unsigned short* map_ptr = (unsigned short*)MAP_BASE_ADR(31);

void prepare_vram()
{		
	copy_words(_palette, BG_PALETTE, sizeof(_palette) / (sizeof(int)));
	
	for(int i=0;i<array_length(_palette);i++)
	{
		unsigned int f = 0x11111111 * i;
		fill_words(&f, &gfx_ptr[0x10*i], 8); // fill a tile with color i
	}

	map_ptr[0] = map_ptr[1] = 0x0000;
	fill_words(&map_ptr[0], map_ptr, 32*32*2 / (sizeof(int)));
}

void init_video()
{
	BGCTRL[0] = SCREEN_BASE(31);
	SetMode(MODE_0 | BG0_ON);
}