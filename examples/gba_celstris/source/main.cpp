#include <gba.h>
#include <stdio.h>

#include "log.hpp"
#include "video_config.hpp"
#include "keys.hpp"
#include "cels_bindings.hpp"


#define CELS_DEFAULTS
#define CELS_ERROR_HANDLER ([](const char* message){ nogba_write_log(message); while(1);})
//#define CELS_NAMED // log function names when calling (debug only)
#include "cels_stack.hpp"

#include "cels_scripts.hpp"

Celesta::CelsRuntime<4> cels_runtime{CELS_ERROR_HANDLER};

int main(void) {		
	irqInit();
	irqEnable(IRQ_VBLANK);	
	nogba_write_log("GBA init");
	
	prepare_vram();
	init_video();
	
	Celstris::State state{};
	
	auto* ctrl = cels_runtime.main_ctrl();
	
	auto* frame = ctrl->push<Celstris::main_loop>();
	frame->params.state = &state;
	ctrl->call(frame, Celstris::main_loop::f0, nullptr, nullptr);
	
	while(true)
	{
		VBlankIntrWait();
		Celstris::main_draw(&state);
		update_keys();
		if(!cels_runtime.run_step())
			break;
	}
	ctrl->pop();
	
	nogba_write_log("Done.");
	while(1) VBlankIntrWait();
	
	
	return 0;
}