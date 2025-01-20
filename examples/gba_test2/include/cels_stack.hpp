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
		Stack(int* buffer = nullptr, int size=0): buffer{buffer}, N{size} {}
		
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
	
	typedef void (*error_handler_t)(const char* message);
	typedef ExecutionController* (*find_free_controller_handler_t)(void* runtime);
	typedef void (*release_controller_handler_t)(void* runtime, void* ctrl);
	
	bool default_suspend_condition() { return false; }
	void default_error_handler(const char* message)	{ while(1); }
	
	#define REG_NOCASH_LOG      (*(unsigned char volatile*)(0x04FFFA1C))
	void debug(const char* message, const char* name)
	{
		while(*message) REG_NOCASH_LOG = *message++;
		REG_NOCASH_LOG = ' ';
		if(name!=nullptr)
			while(*name) REG_NOCASH_LOG = *name++;
		REG_NOCASH_LOG = '\n';
	}

	#ifdef CELS_NAMED
	struct ICelsNamed
	{
		virtual const char* icels_name() { return ""; }
	};
	#endif
	
	struct ExecutionController
	{
	private:
		Stack* stack;		
		ExecutionContext crt_ctx;
		bool must_suspend = false;
		bool (*suspend_condition)();
		
		void* runtime;
		find_free_controller_handler_t find_free_controller_handler;
		release_controller_handler_t release_controller_handler;
		
		template<typename T>
		T error(const char* message)
		{
			if(error_handler) error_handler(message);
			while(1);
			return T();
		}
		
	public:
		ExecutionController(Stack* stack=nullptr, 
			bool (*suspend_condition)() = default_suspend_condition,
			error_handler_t error_handler = default_error_handler,
			void* runtime = nullptr,
			find_free_controller_handler_t find_free_controller_handler = nullptr,
			release_controller_handler_t release_controller_handler = nullptr
		)   : stack{stack}
			, suspend_condition{suspend_condition}			
			, runtime{runtime}
			, find_free_controller_handler{find_free_controller_handler}
			, release_controller_handler{release_controller_handler}
			, error_handler{error_handler}
			{}
		
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
			#ifdef CELS_NAMED
			debug("CALL", ((ICelsNamed*)e_ctx.context)->icels_name());
			#endif
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
			#ifdef CELS_NAMED
			if(crt_ctx.context!=nullptr)
				debug("RET FROM", ((ICelsNamed*)(crt_ctx.context))->icels_name());
			#endif
			pop();			
			jump(return_ctx);
		}
		
		ExecutionController* find_free_controller()
		{
			if(runtime==nullptr)
				return error<ExecutionController*>("No runtime set");
			if(find_free_controller_handler==nullptr)
				return error<ExecutionController*>("No find controller handler set");
			return find_free_controller_handler(runtime);
		}
		
		void release_from_runtime()
		{
			if(runtime==nullptr)
				error<void>("No runtime set");
			if(release_controller_handler==nullptr)
				error<void>("No release controller handler set");
			release_controller_handler(runtime, this);
		}
	};
		
	struct TaskState
	{
		ExecutionController* ctrl;
		void* task_ctx = nullptr;
		void (*on_detach)(void* ctx) = nullptr;
		
		void init(ExecutionController* launching_controller)
		{
			ctrl = launching_controller->find_free_controller();
		}
		
		
	};
	
	template<typename PF, typename MF, typename R>
	struct MultiframeTaskRunner;
	
	
	template<typename T>
	struct Task
	{
		TaskState state;
		T result;
		
		template<typename PF, typename MF>
		Task& init(ExecutionController* launching_controller, PF* launching_ctx, void (*set_params)(PF*, MF*)=[](PF*, MF*){})
		{			
			state.init(launching_controller);
			auto* task_ctx = state.ctrl->push<MultiframeTaskRunner<PF, MF, T>>();
			task_ctx->task = this;
			task_ctx->parent_ctx = launching_ctx;
			task_ctx->set_params = set_params;						
			state.ctrl->call(task_ctx, MultiframeTaskRunner<PF, MF, T>::f0, nullptr, nullptr);
			
			state.task_ctx =task_ctx;
			state.on_detach = [](void* _task_ctx)
			{
				auto* task_ctx = (MultiframeTaskRunner<PF, MF, T>*)_task_ctx;
				task_ctx->task = nullptr;
			};
			
			return *this;
		}		
		
		void detach()
		{
			if(state.on_detach) state.on_detach(state.task_ctx);
		}
		
	};
	
	template<>
	struct Task<void>
	{
		TaskState state;
		
		template<typename PF, typename MF>
		Task& init(ExecutionController* launching_controller, PF* launching_ctx, void (*set_params)(PF*, MF*)=[](PF*, MF*){})
		{
			state.init(launching_controller);
			auto* task_ctx = state.ctrl->push<MF>();
			set_params(launching_ctx, task_ctx);
			state.ctrl->call(task_ctx, MF::f0, nullptr, nullptr);
			
			state.task_ctx =task_ctx;
			state.on_detach = [](void* _task_ctx)
			{
				auto* task_ctx = (MultiframeTaskRunner<PF, MF, void>*)_task_ctx;
				task_ctx->task = nullptr;
			};
			return *this;
		}
		
		void detach()
		{
			if(state.on_detach) state.on_detach(state.task_ctx);
		}
		
	};
	
	template<typename T>
	struct is_void
	{
		inline static constexpr bool value = false;
	};
	
	template<>
	struct is_void<void>
	{
		inline static constexpr bool value = true;
	};
	
	template<typename PF, typename MF, typename R>
	struct MultiframeTaskRunner 
	#ifdef CELS_NAMED
		: public ICelsNamed
	#endif
	{
		Task<R>* task;
		PF* parent_ctx;
		void (*set_params)(PF*, MF*)=[](PF*, MF*){};
		
		static void f0(void* _ctx, Celesta::ExecutionController* ctrl)
		{
			auto* ctx = (MultiframeTaskRunner<PF, MF, R>*)_ctx;
			auto* f = ctrl->push<MF>();
			ctx->set_params(ctx->parent_ctx, f);
			ctrl->call(f, MF::f0, ctx, f1);
			return;			
		}
		
		static void f1(void* _ctx, Celesta::ExecutionController* ctrl)
		{
			auto* ctx = (MultiframeTaskRunner<PF, MF, R>*)_ctx;
			{
				auto* f = ctrl->peek<MF>();
				if constexpr(!is_void<R>::value)
				{
					if(ctx->task)
						ctx->task->result = f->return_value;
				}				
			}
			ctrl->pop();
			ctrl->ret();
		}
		
		#ifdef CELS_NAMED
		const char* icels_name() override { return "Task"; }
		#endif
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
	
	template<int N>
	struct busy_bucket_t
	{
		char buffer[N]{};
		
		int get_free_index()
		{
			for(int i=0;i<N;i++)
			{
				if(buffer[i]!=0) continue;				
				buffer[i] = 1;
				return i;				
			}
			return -1;
		}
		
		void release_index(int i)
		{
			buffer[i] = 0;
		}
	};
	
	template<int NO_CTRLS, int STACK_SIZE = 1024>
	struct CelsRuntime
	{
		static_assert(NO_CTRLS > 0);
		
		int stack_buffers[NO_CTRLS][STACK_SIZE]{};
		Stack stacks[NO_CTRLS];
		ExecutionController ctrls[NO_CTRLS];
		
		
		busy_bucket_t<NO_CTRLS> busy_bucket;		
		
		void (*error_handler)(const char*) = [](const char*) { while(1); };
		
		CelsRuntime()
		{
			for(int i=0;i<NO_CTRLS;i++)
			{
				stacks[i] = Stack(stack_buffers[i], sizeof(stack_buffers[i])/sizeof(stack_buffers[i][0]));
				ctrls[i] = ExecutionController(&stacks[i]
					, default_suspend_condition
					, default_error_handler
					, this // runtime
					, find_free_controller_handler
					);
			}
			
			// controller 0 (main) is always busy
			busy_bucket.buffer[0] = 1;
		}
		
		ExecutionController* find_free_controller()
		{
			int index = busy_bucket.get_free_index();
			if(index<0)
			{
				if(error_handler)
					error_handler("Controllers busy");
				while(1);
				return nullptr;
			}
			return &ctrls[index];
		}
		
		void release_controller(ExecutionController* ctrl)
		{
			int index = ctrl - &ctrls[0];
			if(index<0 || index>=NO_CTRLS)
			{
				if(error_handler)
					error_handler("Controller not managed by runtime");
				while(1);				
			}
		}
		
		void set_error_handler(void (*error_handler)(const char*))
		{
			this->error_handler = error_handler;
			for(int i=0;i<NO_CTRLS;i++)
				ctrls[i].error_handler = error_handler;
		}
		
		static ExecutionController* find_free_controller_handler(void* runtime)
		{
			return ((CelsRuntime<NO_CTRLS, STACK_SIZE>*)runtime)->find_free_controller();
		}
		
		int run_step()
		{
			int result = 0;
			for(int i=0;i<NO_CTRLS;i++)
			{
				if(busy_bucket.buffer[i]==0) continue;
				result += ctrls[i].run_step();
			}
			return !!result;
		}
		
		ExecutionController* main_ctrl() { return &ctrls[0]; }
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