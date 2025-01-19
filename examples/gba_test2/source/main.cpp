#include <gba.h>
#include <stdio.h>

#define REG_NOCASH_LOG      (*(unsigned char volatile*)(0x04FFFA1C))
void nogba_write_log(const char* message)
{
	while(*message) REG_NOCASH_LOG = *message++;
	REG_NOCASH_LOG = '\n';
}

#define CELS_DEFAULTS
#define CELS_ERROR_HANDLER ([](const char* message){ nogba_write_log(message); while(1);})
#include "cels_stack.hpp"

auto& cels_ctrl = Celesta::DefaultConfig::controller;

#include "celstris.hpp"
#include "cels_scripts.hpp"


int bk_key_down = 0;
int bk_key_held = 0;

int Celstris::left_key_down() { return (bk_key_down & KEY_LEFT)!=0;}

int Celstris::right_key_down() { return (bk_key_down & KEY_RIGHT)!=0;}

int Celstris::down_key_held() { return (bk_key_held & KEY_DOWN)!=0;}

unsigned short shadow_map[32*32]{};

#include "scene.hpp"

void draw(Celstris::GameState* state)
{
	state->push_piece();
	CpuFastSet(shadow_map, MAP_BASE_ADR(31), COPY32 | sizeof(shadow_map));
	state->pop_piece();
	scanKeys();
		
	bk_key_down = keysDown();
	bk_key_held = keysHeld();	
	if(Celstris::left_key_down()) nogba_write_log("LEFT");
	if(Celstris::down_key_held()) nogba_write_log("DOWN");
}

struct Setup
{	
	
	inline static void draw(Celstris::State* state)
	{
		void* map_base = ((unsigned short*)MAP_BASE_ADR(31));
		void* shadow_data = state->shadow_map.data();
		CpuFastSet(shadow_data, map_base, COPY32 | (state->shadow_map.length/2));
	}
	
	inline static auto create_scene(Celstris::State* state)
	{
		return Scene<
			Celstris::State,
			Setup::draw, Celstris::main_loop, VBlankIntrWait
		>(state, &cels_ctrl);
	}
};
	

int main(void) {
	irqInit();
	irqEnable(IRQ_VBLANK);	
	nogba_write_log("GBA init");
	
	BG_PALETTE[0x00] = RGB8(0x00,0x00,0x00);
	BG_PALETTE[0x01] = RGB8(0x40,0x80,0xc0);
	BG_PALETTE[0x02] = RGB8(0xFF,0xFF,0xFF);
	BG_PALETTE[0x03] = RGB8(0xF5,0xFF,0xFF);
	BG_PALETTE[0x04] = RGB8(0xDF,0xFF,0xF2);	
	BG_PALETTE[0x05] = RGB8(0xCA,0xFF,0xE2);
	BG_PALETTE[0x06] = RGB8(0xB7,0xFD,0xD8);
	BG_PALETTE[0x07] = RGB8(0x2C,0x4F,0x8B);
	
	for(int i=0;i<8;i++)
	{
		unsigned int f = 0x11111111 * i;
		CpuFastSet(&f, (char*)MAP_BASE_ADR(0)+i*(0x20), FILL | COPY32 | (0x10/2));
	}
	
	// clear screen map with tile 0 ('space' tile) (256x256 halfwords)
	*((u32*)MAP_BASE_ADR(31)) = 0;
	CpuFastSet(MAP_BASE_ADR(31), MAP_BASE_ADR(31), FILL | COPY32 | (0x800/4));
	
	Celstris::GameState game_state(shadow_map, 32, 15-10/2, 0, 10, 18);
	
	int x0 = 15-game_state.board_width/2;
	int x1 = 15+game_state.board_width/2;
	for(int y=0;y<game_state.board_height;y++)
	{		
		shadow_map[y*32+x0-1] = shadow_map[y*32+x1] = 0x0001;
	}
	for(int x=x0-1;x<=x1;x++)
	{
		shadow_map[game_state.board_height*32+x] = 0x0001;
	}
	
	//for(int x=2;x<7;x++) shadow_map[13*32+x]=0x0002;
	
	BGCTRL[0] = SCREEN_BASE(31);
	SetMode(MODE_0 | BG0_ON);
	
	Celstris::State state;
	
	Setup::create_scene(&state)
		.init()
		.run();
	
	nogba_write_log("Done.");
	while(1) 
	{
		VBlankIntrWait();
	}
	
	return 0;
}


