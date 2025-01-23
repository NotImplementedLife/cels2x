#pragma once
#include <gba.h>

inline int shadow_keysDown;
inline int shadow_keysHeld;

void update_keys()
{
	scanKeys();
	shadow_keysDown = keysDown();
	shadow_keysHeld = keysHeld();
}