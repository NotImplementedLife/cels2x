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

	cels_main(); // calls cels_main() from celstris.cels
	
	nogba_write_log("Done.");
	while(1) VBlankIntrWait();
	
	
	return 0;
}