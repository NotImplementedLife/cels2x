#pragma once

#include <gba.h>

void copy_words(const void* src, void* dest, int words_count)
{
	CpuFastSet(src, dest, COPY32 | words_count);
}

void fill_words(const void* src, void* dest, int words_count)
{
	CpuFastSet(src, dest, FILL | COPY32 | words_count);
}

template<typename T, int N>
inline static constexpr int array_length(T (&array)[N]) { return N; }
