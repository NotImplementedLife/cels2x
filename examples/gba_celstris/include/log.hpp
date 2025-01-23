#pragma once

#define REG_NOCASH_LOG      (*(unsigned char volatile*)(0x04FFFA1C))
void nogba_write_log(const char* message)
{
	while(*message) REG_NOCASH_LOG = *message++;
	REG_NOCASH_LOG = '\n';
}