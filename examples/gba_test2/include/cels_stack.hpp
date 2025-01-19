#pragma once
#include <new>

namespace Celesta
{		
	struct Stack
	{
	private:
		int* buffer;
		int N;		
		int top = 0;
		
		void* push(int bytes_size, int align)
		{			
			int return_index = top;
			align = (align+3)/4;
			int r = top%align;
			if(r>0) top+=align-r;			
			int ints_size = (bytes_size+3)/4;
			if(top+ints_size+1>N) return nullptr;
			
			int* offset = &buffer[top];
			top += ints_size;
			buffer[top] = return_index;
			top++;
			
			return offset;
		}
		
		void* peek(int bytes_size)
		{
			int ints_size = (bytes_size+3)/4;
			int index = top - 1 - ints_size;
			if(index<0) return nullptr;
			return &buffer[index];			
		}

	public:
		Stack(int* buffer, int size): buffer{buffer}, N{size} {}
		
		template<typename T>
		T* push()
		{
			T* offset = (T*)push(sizeof(T), alignof(T));
			if(offset==nullptr) return nullptr;
			return new (offset) T();
		}
		
		template<typename T>
		T* peek()
		{
			return (T*)peek(sizeof(T));			
		}
		
		bool pop()
		{
			if(top>0)			
			{
				top = buffer[top-1];
				return true;
			}
			return false;
		}
		
		void debug_print(int (*pf)(const char*,...), int ncols=3)
		{
			pf("____________________\n");
			for(int i=0;i<N;i++)
			{
				pf("%c%08X", top==i?'*':' ', buffer[i]);
				if(i%ncols==ncols-1) pf("\n");
			}
			pf("\n____________________\n");
		}
	};
	
	struct ExecutionController;
	
	typedef void (*FnExecutor)(void*, ExecutionController*);
	
	struct ExecutionContext
	{
		void* context;
		FnExecutor executor;
		
		ExecutionContext(void* context=nullptr, FnExecutor executor=nullptr)
			: context{context}, executor{executor} {}

	};
	
	struct ExecutionController
	{
	private:
		Stack* stack;		
		ExecutionContext crt_ctx;
		bool must_suspend = false;
		bool (*suspend_condition)();
	public:
		ExecutionController(Stack* stack, 
			bool (*suspend_condition)() = [](){ return false; },
			void (*error_handler)(const char* message) = [](const char*){ while(1); }
		) : stack{stack}, suspend_condition{suspend_condition}, error_handler{error_handler} {}
		
		void (*error_handler)(const char* message);
		
		int run_step()
		{
			while(!must_suspend)
			{
				if(crt_ctx.context==nullptr)
					return 0;
				crt_ctx.executor(crt_ctx.context, this);
				if(suspend_condition()) break;
			}
			must_suspend = false;
			return 1;
		}
		
		void suspend()
		{
			must_suspend = true;
		}
				
		void jump(ExecutionContext ectx)
		{
			crt_ctx = ectx;
		}
		
		void jump(void* ctx, FnExecutor ex)
		{
			crt_ctx = ExecutionContext(ctx, ex);
		}
		
		void jump_end()
		{
			crt_ctx = ExecutionContext(nullptr, nullptr);
		}
		
		template<typename CTX>
		CTX* push()
		{
			auto* offset = stack->push<CTX>();
			if(offset==nullptr && error_handler)
			{
				error_handler("Cels: Stack overflow");
			}			
			return offset;
		}
		
		template<typename CTX>
		CTX* peek()
		{
			auto* offset = stack->peek<CTX>();
			if(offset==nullptr && error_handler)
			{
				error_handler("Cels: Stack peek error");
			}
			return offset;
		}
		
		void pop()
		{
			if(!stack->pop() && error_handler)
				error_handler("Cels: Stack pop error");
		}
				
		void call(ExecutionContext e_ctx, ExecutionContext return_ctx)
		{
			*push<ExecutionContext>() = return_ctx;			
			jump(e_ctx);
		}
		
		void call(void* fun_ctx, FnExecutor fun_ex, void* ret_ctx, FnExecutor ret_ex)
		{
			call(ExecutionContext(fun_ctx, fun_ex), ExecutionContext(ret_ctx, ret_ex));
		}
		
		void ret()
		{
			ExecutionContext return_ctx = *peek<ExecutionContext>();
			pop();			
			jump(return_ctx);			
		}
	};
	
	
	template<typename T, int N>
	struct StaticArray
	{
	private:
		T items[N];
	public:
		const T& operator[](int index) const { return items[index]; }
		T& operator[](int index) { return items[index]; }
		
		T* data() { return &items[0]; }
		
		inline static constexpr int length = N;
		inline static constexpr int array_size = N * sizeof(T);
	};
	
#ifdef CELS_DEFAULTS
	
	#ifndef CELS_ERROR_HANDLER
		#define CELS_ERROR_HANDLER ([](const char*){while(1);})
	#endif
	
	struct DefaultConfig
	{
		inline static int stack_buffer[1024]{};
		inline static Stack stack{stack_buffer, sizeof(stack_buffer)/sizeof(stack_buffer[0])};
		
		inline static Celesta::ExecutionController controller{
			&stack,
			/* suspend_condition = */ [](){ return false; },
			/* error_handler     = */ CELS_ERROR_HANDLER
		};
	};

#endif // CELS_DEFAULTS
	
	
}