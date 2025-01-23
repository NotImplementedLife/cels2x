#pragma once

#include "video_config.hpp"
#include <stdlib.h>
#include "keys.hpp"
#include <gba.h>

namespace Celstris::Bindings
{	
	unsigned short pieces[][16] = {
		{
			0, 0, 1, 0,
			0, 0, 1, 0,
			0, 0, 1, 0,
			0, 0, 1, 0,
		},
		{
			0, 0, 0, 0,
			0, 1, 1, 0,
			0, 0, 1, 0,
			0, 0, 1, 0,
		},
		{
			0, 0, 0, 0,
			0, 1, 1, 0,
			0, 1, 0, 0,
			0, 1, 0, 0,
		},
		{
			0, 0, 0, 0,
			0, 1, 1, 1,
			0, 0, 1, 0,
			0, 0, 0, 0,
		},
		{
			0, 0, 0, 0,
			0, 1, 1, 0,
			0, 0, 1, 1,
			0, 0, 0, 0,
		},
		{
			0, 0, 0, 0,
			0, 0, 1, 1,
			0, 1, 1, 0,
			0, 0, 0, 0,
		},
	};
	
	constexpr int PIECES_COUNT = 6;
	
	void load_random_piece(unsigned short* buffer)
	{
		int id = rand() % PIECES_COUNT;
		copy_words(&pieces[id][0], buffer, 8);
	}
	
	void copy_piece_to_map(unsigned short* map, unsigned short* piece, int y, int x)
	{
		for(int i=0;i<4;i++)
		{
			for(int j=0;j<4;j++)
			{
				if(piece[4*i+j]!=0)
					map[32*(y+i)+(x+j)] = piece[4*i+j];
			}
		}
	}
	
	void copy_piece_to_vram(unsigned short* piece, int y, int x)
	{
		for(int i=0;i<4;i++)
		{
			for(int j=0;j<4;j++)
			{
				if(piece[4*i+j]!=0)
					map_ptr[32*(y+i)+(x+j)] = piece[4*i+j];
			}
		}
	}
	
	bool test_piece_placement(unsigned short* map, int mx, int my, int mw, int mh, unsigned short* piece, int y, int x)
	{		
		for(int i=0;i<4;i++)
		{
			int iy = y+i;			
			for(int j=0;j<4;j++)
			{
				int ix = x+j;
				if(piece[4*i+j]!=0)
				{
					if(!(my<=iy && iy<my+mh)) return false;
					if(!(mx<=ix && ix<mx+mw)) return false;
					if(map[32*iy+ix]!=0) return false;
				}
			}
		}
		return true;
	}	
	
	
	void copy_map_to_vram(unsigned short* shadow_map)
	{
		copy_words(shadow_map, map_ptr, 32*32*2 / (sizeof(int)));
	}
	
	bool left_key_down() { return shadow_keysDown & KEY_LEFT; }
	bool right_key_down() { return shadow_keysDown & KEY_RIGHT; }
	bool down_key_held() { return shadow_keysHeld & KEY_DOWN; }
	
}