#pragma once

#define REG_NOCASH_LOG      (*(unsigned char volatile*)(0x04FFFA1C))
void nogba_write_log(const char* message)
{
	while(*message) REG_NOCASH_LOG = *message++;
	REG_NOCASH_LOG = '\n';
}

void log_msg(const char* message, const char* message2)
{
	while(*message) REG_NOCASH_LOG = *message++;
	REG_NOCASH_LOG = ' ';
	while(*message2) REG_NOCASH_LOG = *message2++;
	REG_NOCASH_LOG = '\n';
}

static const char* const hex_str = "0123456789ABCDEF";

void log_offset(const char* message, const void* x)
{		
	unsigned n = (unsigned)x;
	char c[17]{};
	char *it = &c[16];
	*--it = '\0';
	
	for(int i=0;i<8;i++)
	{
		*--it = hex_str[n & 0xF];
		n>>=4;
	}
	log_msg(message, it);
}
