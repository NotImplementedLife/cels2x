#pragma once

#include "video_config.hpp"

namespace Celstris::Bindings
{
	void copy_map_to_vram(unsigned short* shadow_map)
	{
		copy_words(shadow_map, map_ptr, 32*32*2 / (sizeof(int)));
	}
}