// package: global::Example
namespace Example
{
    inline int sum(int* v, int n)
    {
        int s_l1;
        
        s_l1 = ((int)0);
        int i_l2;
        
        i_l2 = ((int)0);
        while ((i_l2 < n)) {
            s_l1 = (s_l1 + v[i_l2]);
            i_l2 = (i_l2 + ((int)1));
        }
        
        return s_l1;
    }
    
    /* multiframe function fn~global::Example::sum_multiframe */
    struct sum_multiframe_mf
    {
        struct
        {
            int* v;
            int n;
        } params;
        int return_value;
        int s_l3;
        int i_l4;
        inline static void f0(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (sum_multiframe_mf*)_ctx;
            goto L_1;
            L_1:
            goto L_15;
            L_15:
            ctrl->jump(ctx, sum_multiframe_mf::f1); return;
        }
        
        inline static void f1(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (sum_multiframe_mf*)_ctx;
            goto L_2;
            L_2:
            
            ctx->s_l3 = ((int)0);
            
            ctx->i_l4 = ((int)0);
            goto L_16;
            L_16:
            ctrl->jump(ctx, sum_multiframe_mf::f2); return;
        }
        
        inline static void f2(void* _ctx, Celesta::ExecutionController* ctrl)
        {
            auto* ctx = (sum_multiframe_mf*)_ctx;
            goto L_8;
            L_8:
            if((ctx->i_l4 < ctx->params.n))
                goto L_10; else goto L_9;
            L_10:
            ctx->s_l3 = (ctx->s_l3 + ctx->params.v[ctx->i_l4]);
            ctx->i_l4 = (ctx->i_l4 + ((int)1));
            ctrl->suspend();
            
            goto L_14;
            L_14:
            ctrl->jump(ctx, sum_multiframe_mf::f2); return;
            L_9:
            ctx->return_value = ctx->s_l3;
            ;
            ctrl->ret(); return;
            
            goto L_3;
            L_3:
            ctrl->ret(); return;
        }
        
    };

}
