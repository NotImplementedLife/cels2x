#include <gba.h>
#include <stdio.h>

#include "cels_stack.hpp"

#define REG_NOCASH_LOG      (*(unsigned char volatile*)(0x04FFFA1C))

void nogba_write_log(const char* message)
{
	while(*message) REG_NOCASH_LOG = *message++;
	REG_NOCASH_LOG = '\n';
}

int cels_stack_buffer[1024]{};
Celesta::Stack cels_stack(cels_stack_buffer, sizeof(cels_stack_buffer)/sizeof(cels_stack_buffer[0]));

Celesta::ExecutionController cels_ctrl = ([]()
{
	auto ctrl = Celesta::ExecutionController(&cels_stack, [](){ return 0 && REG_VCOUNT>160; });
	ctrl.error_handler = [](const char* message){
		nogba_write_log(message);
		while(1);
	};
	return ctrl;
})();


#include "celstris.hpp"
#include "cels_scripts.hpp"
// #include "celstris.cels.hpp"

int bk_key_down = 0;
int bk_key_held = 0;

int Celstris::left_key_down() { return (bk_key_down & KEY_LEFT)!=0;}

int Celstris::right_key_down() { return (bk_key_down & KEY_RIGHT)!=0;}

int Celstris::down_key_held() { return (bk_key_held & KEY_DOWN)!=0;}


unsigned short shadow_map[32*32]{};

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
	//Celstris::GameState game_state(shadow_map, 32, 0,0, 10, 18);
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
		
	auto* f = cels_ctrl.push<Celstris::main_loop_mf>();
	f->params.gs = &game_state;	
	cels_ctrl.call(f, Celstris::main_loop_mf::f0, nullptr, nullptr);

	
	while(1) 
	{
		VBlankIntrWait();
		game_state.push_piece();
		CpuFastSet(shadow_map, MAP_BASE_ADR(31), COPY32 | sizeof(shadow_map));
		game_state.pop_piece();
		
		scanKeys();
		
		bk_key_down = keysDown();
		bk_key_held = keysHeld();	
		if(Celstris::left_key_down()) nogba_write_log("LEFT");
		if(Celstris::down_key_held()) nogba_write_log("DOWN");
		
		if(!cels_ctrl.run_step()) break;
	}
	
	nogba_write_log("Done.");
	while(1) 
	{
		VBlankIntrWait();
	}
	
	/*
	int buffer[50]{};	
	Celesta::Stack stack(buffer, sizeof(buffer)/sizeof(buffer[0]));
	Celesta::ExecutionController E(&stack, [](){ return 0 || REG_VCOUNT>220; });
	E.error_handler = [](const char* message){
		iprintf(message);
		while(1);
	};
	
	auto* f = E.push<Test::main_mf>();	
	//f->params.a = 75;
	//f->params.b = 35;
	E.call(f, Test::main_mf::f0, nullptr, nullptr);
	
	int frameid=0;
	bool running=true;
	int vbc0, vbc;
	while(running)
	{
		VBlankIntrWait();
		iprintf("Frame %i %i\n", vbc0, vbc);
		vbc0 = REG_VCOUNT;
		if(!E.run_step()) running=false;		
		vbc = REG_VCOUNT;		
		//iprintf("Frame %i %i %i\n", frameid++, vbc0, vbc);
	}
	
	
	iprintf("Done.\n");
	//iprintf("d = %i\n", f->return_value);

	while (1) { 
		VBlankIntrWait();
	}*/
}


