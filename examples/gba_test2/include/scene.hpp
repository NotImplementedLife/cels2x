#pragma once

#include "cels_stack.hpp"

template<typename State, auto Draw, typename Frame, auto WaitForVBlank>
struct Scene
{
private:
	State* state;
	Celesta::ExecutionController* ctrl;
	Frame* frame;
		
public:
	Scene(State* state, Celesta::ExecutionController* ctrl=nullptr)
		: state{state}
		, ctrl{ctrl}
	{
	}
		
	
	auto& init()
	{
		frame = ctrl->push<Frame>();
		frame->params.gs = state;
		ctrl->call(frame, Frame::f0, nullptr, nullptr);
		return *this;
	}
	
	int run_frame()
	{
		WaitForVBlank();
		Draw(state);
		return ctrl->run_step();
	}
	
	auto& run()
	{
		while(run_frame());
		return *this;
	}
};

template<auto F>
struct FuncWrapper
{
	inline static constexpr auto value = F;
};

template<typename State, auto Draw, 
	auto Frame, auto WaitForVBlank>
struct Scene<State, Draw, FuncWrapper<Frame>, WaitForVBlank>
{
private:
	State* state;
public:
	Scene(State* state, Celesta::ExecutionController* ctrl=nullptr) : state{state} {}

	auto& init() { return *this; }
	
	int run_frame()
	{
		WaitForVBlank();
		Draw(state);
		return Frame(state);
	}
	
	auto& run()
	{		
		while(run_frame());
		return *this;
	}
};


/*template<
	typename State,
	void (*Draw)(State*),
	int (*Frame)(State*),
	void (*WaitForVBlank)()
>
struct Scene<State, Draw, Frame, WaitForVBlank>
{
private:
	State* state;
public:
	Scene(State* state) : state{state} {}
	
	int run_frame()
	{
		WaitForVBlank();
		Draw(state);
		return Frame(state);
	}
	
	void run()
	{		
		while(run_frame());
	}
};

#include "cels_stack.hpp"

template<
	typename State,
	void (*Draw)(State*),
	typename Frame,
	void (*WaitForVBlank)()
>
struct Scene<State, Draw, Frame, WaitForVBlank>
{
private:
	State* state;
	Celesta::ExecutionController* ctrl;
	Frame* frame;
public:
	Scene(State* state, Celesta::ExecutionController* ctrl) 
		: state{state}
		, ctrl{ctrl}
	{
		frame = ctrl->push<Frame>();
		frame->params.gs = state;
		ctrl->call(frame, Frame::f0, nullptr, nullptr);
	}
	
	int run_frame()
	{
		WaitForVBlank();
		Draw(state);
		return frame->run_step();
	}
	
	void run()
	{		
		while(run_frame());
	}
};*/