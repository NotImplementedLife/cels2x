#include <gba.h>
#include <stdio.h>

#include "log.hpp"
#include "video_config.hpp"
#include "cels_bindings.hpp"


#define CELS_DEFAULTS
#define CELS_ERROR_HANDLER ([](const char* message){ nogba_write_log(message); while(1);})
//#define CELS_NAMED
#include "cels_stack.hpp"

auto& cels_ctrl = Celesta::DefaultConfig::controller;


int dir_x(int keys)
{
	if(keys & KEY_LEFT) return -1;
	if(keys & KEY_RIGHT) return 1;
	return 0;
}

int dir_y(int keys)
{
	if(keys & KEY_UP) return -1;
	if(keys & KEY_DOWN) return 1;
	return 0;
}

#include "celstris.hpp"
#include "cels_scripts.hpp"


int bk_key_down = 0;
int bk_key_held = 0;

unsigned short keysDown2()
{
	return bk_key_down;
}

int Celstris::left_key_down() { return (bk_key_down & KEY_LEFT)!=0;}

int Celstris::right_key_down() { return (bk_key_down & KEY_RIGHT)!=0;}

int Celstris::down_key_held() { return (bk_key_held & KEY_DOWN)!=0;}

unsigned short shadow_map[32*32]{};

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
		/*unsigned short* map_base = ((unsigned short*)MAP_BASE_ADR(31));
		void* shadow_data = state->shadow_map.data();
		CpuFastSet(shadow_data, map_base, COPY32 | (state->shadow_map.length/2));
		map_base[state->npc_y*32 + state->npc_x] = 0x06;
		map_base[state->player_y*32 + state->player_x] = state->player_color;*/
	}
};
	

int main(void) {
	irqInit();
	irqEnable(IRQ_VBLANK);	
	nogba_write_log("GBA init");
	
	prepare_vram();
	init_video();
	
	Celstris::State state{};	
	
	Celesta::CelsRuntime<4> cels_runtime;
	cels_runtime.set_error_handler(CELS_ERROR_HANDLER);
	
	auto* ctrl = cels_runtime.main_ctrl();
	
	auto* frame = ctrl->push<Celstris::main_loop>();
	frame->params.state = &state;
	ctrl->call(frame, Celstris::main_loop::f0, nullptr, nullptr);
	
	while(1) 
	{
		VBlankIntrWait();
		Celstris::main_draw(&state);
		scanKeys();
		bk_key_down = keysDown();
		if(!cels_runtime.run_step())
			break;
	}
	
	nogba_write_log("Done.");
	while(1) VBlankIntrWait();
	
	/*Celstris::GameState game_state(shadow_map, 32, 15-10/2, 0, 10, 18);
	
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
	
	Celstris::State state{};	
	
	Celesta::CelsRuntime<4> cels_runtime;
	cels_runtime.set_error_handler(CELS_ERROR_HANDLER);
	
	auto* ctrl = cels_runtime.main_ctrl();
	
	auto* frame = ctrl->push<Celstris::main_loop>();
	frame->params.state = &state;
	ctrl->call(frame, Celstris::main_loop::f0, nullptr, nullptr);
	
	while(1)
	{
		VBlankIntrWait();		
		Setup::draw(&state);
		scanKeys();
		bk_key_down = keysDown();
		if(!cels_runtime.run_step())
			break;		
	}
	
	nogba_write_log("Done.");
	while(1) 
	{
		VBlankIntrWait();
	}*/
	
	return 0;
}