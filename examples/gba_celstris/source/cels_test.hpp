#include "cels_stack.hpp"

// package: global::Celstris
namespace Celstris
{
    struct Piece;
    
    struct GameState;
    
    extern Celstris::Piece* GameState_generate_random_piece(Celstris::GameState* gs);
    
    extern int GameState_test_piece(Celstris::GameState* gs, Celstris::Piece* piece);
    
    extern void GameState_place_piece(Celstris::GameState* gs, Celstris::Piece* piece);
    
    extern void GameState_reset(Celstris::GameState* gs);
    
    extern void Piece_move_x(Celstris::Piece* piece, int dx);
    
    extern void Piece_move_y(Celstris::Piece* piece, int dy);
    
    extern int left_key_down();
    
    extern int right_key_down();
    
    extern int down_key_held();
    
    /* multiframe function fn~global::Celstris::process_user_input */
    struct process_user_input_mf
    {
        struct
        {
            Celstris::GameState* gs;
            Celstris::Piece* piece;
        } params;
        int i_l1;
        int dx_l2;
        inline static void f0(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (process_user_input_mf*)_ctx;
            goto L_1;
            L_1:
            goto L_32;
            L_32:
            ctrl->jump(ctx, process_user_input_mf::f1); return;
        }
        
        inline static void f1(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (process_user_input_mf*)_ctx;
            goto L_2;
            L_2:
            
            ctx->i_l1 = ((int)0);
            goto L_33;
            L_33:
            ctrl->jump(ctx, process_user_input_mf::f2); return;
        }
        
        inline static void f2(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (process_user_input_mf*)_ctx;
            goto L_6;
            L_6:
            if((ctx->i_l1 < ((int)10)))
                goto L_7; else goto L_3;
            L_7:
            
            ctx->dx_l2 = ((int)0);
            goto L_10;
            L_10:
            if((Celstris::left_key_down() != ((int)0)))
                goto L_17; else goto L_16;
            L_17:
            ctx->dx_l2 = (((int)0) - ((int)1));
            goto L_16;
            L_16:
            goto L_11;
            L_11:
            if((Celstris::right_key_down() != ((int)0)))
                goto L_19; else goto L_18;
            L_19:
            ctx->dx_l2 = ((int)1);
            goto L_18;
            L_18:
            goto L_12;
            L_12:
            if((ctx->dx_l2 != ((int)0)))
                goto L_21; else goto L_20;
            L_21:
            Celstris::Piece_move_x(ctx->params.piece, ctx->dx_l2);
            
            goto L_23;
            L_23:
            if((Celstris::GameState_test_piece(ctx->params.gs, ctx->params.piece) == ((int)0)))
                goto L_25; else goto L_24;
            L_25:
            Celstris::Piece_move_x(ctx->params.piece, (((int)0) - ctx->dx_l2));
            
            goto L_24;
            L_24:
            goto L_20;
            L_20:
            goto L_13;
            L_13:
            if((Celstris::down_key_held() != ((int)0)))
                goto L_27; else goto L_26;
            L_27:
            Celstris::Piece_move_y(ctx->params.piece, ((int)1));
            
            goto L_29;
            L_29:
            if((Celstris::GameState_test_piece(ctx->params.gs, ctx->params.piece) == ((int)0)))
                goto L_31; else goto L_30;
            L_31:
            Celstris::Piece_move_y(ctx->params.piece, (((int)0) - ((int)1)));
            
            goto L_30;
            L_30:
            goto L_26;
            L_26:
            goto L_14;
            L_14:
            ctx->i_l1 = (ctx->i_l1 + ((int)1));
            ctrl->suspend();
            
            goto L_34;
            L_34:
            ctrl->jump(ctx, process_user_input_mf::f2); return;
            L_3:
            ctrl->ret(); return;
        }
        
    };
    
    /* multiframe function fn~global::Celstris::main_loop */
    struct main_loop_mf
    {
        struct
        {
            Celstris::GameState* gs;
        } params;
        int running_l3;
        Celstris::Piece* piece_l4;
        int falling_down_l5;
        inline static void f0(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_1;
            L_1:
            goto L_28;
            L_28:
            ctrl->jump(ctx, main_loop_mf::f1); return;
        }
        
        inline static void f1(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_2;
            L_2:
            
            ctx->running_l3 = ((int)1);
            goto L_29;
            L_29:
            ctrl->jump(ctx, main_loop_mf::f2); return;
        }
        
        inline static void f2(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_6;
            L_6:
            if((ctx->running_l3 > ((int)0)))
                goto L_7; else goto L_3;
            L_7:
            
            ctx->piece_l4 = Celstris::GameState_generate_random_piece(ctx->params.gs);
            goto L_10;
            L_10:
            if((Celstris::GameState_test_piece(ctx->params.gs, ctx->piece_l4) > ((int)0)))
                goto L_12; else goto L_13;
            L_12:
            
            ctx->falling_down_l5 = ((int)1);
            goto L_30;
            L_30:
            ctrl->jump(ctx, main_loop_mf::f3); return;
            L_13:
            Celstris::GameState_reset(ctx->params.gs);
            
            goto L_31;
            L_31:
            ctrl->jump(ctx, main_loop_mf::f5); return;
            L_3:
            ctrl->ret(); return;
        }
        
        inline static void f3(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_16;
            L_16:
            if((ctx->falling_down_l5 > ((int)0)))
                goto L_18; else goto L_17;
            L_18:
            {
            	auto* f = ctrl->push<Celstris::process_user_input_mf>();
            	f->params.gs = ctx->params.gs;
            	f->params.piece = ctx->piece_l4;
            	ctrl->call(f, Celstris::process_user_input_mf::f0, ctx, main_loop_mf::f4);
            	return;
            }
            
            goto L_33;
            L_33:
            ctrl->jump(ctx, main_loop_mf::f4); return;
            L_17:
            Celstris::GameState_place_piece(ctx->params.gs, ctx->piece_l4);
            
            goto L_34;
            L_34:
            ctrl->jump(ctx, main_loop_mf::f5); return;
        }
        
        inline static void f4(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_27;
            L_27:
            ctrl->pop();
            
            Celstris::Piece_move_y(ctx->piece_l4, ((int)1));
            ;
            goto L_21;
            L_21:
            if((Celstris::GameState_test_piece(ctx->params.gs, ctx->piece_l4) == ((int)0)))
                goto L_23; else goto L_22;
            L_23:
            Celstris::Piece_move_y(ctx->piece_l4, (((int)0) - ((int)1)));
            ;
            ctx->falling_down_l5 = ((int)0);
            goto L_22;
            L_22:
            goto L_35;
            L_35:
            ctrl->jump(ctx, main_loop_mf::f3); return;
        }
        
        inline static void f5(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (main_loop_mf*)_ctx;
            goto L_11;
            L_11:
            goto L_32;
            L_32:
            ctrl->jump(ctx, main_loop_mf::f2); return;
        }
        
    };

}
