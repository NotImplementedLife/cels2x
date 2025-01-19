#pragma once
#include <stdlib.h>

namespace Celstris
{	
	struct BufferView
	{
	private:
		unsigned short* start;
		int stride;
	public:
		BufferView(unsigned short* start=nullptr, int stride=0) : start{start}, stride{stride} { }
		unsigned short* operator[](int y){ return &start[stride*y]; }				
	};
	
	struct Piece
	{				
		unsigned short data[16]{};
		int x=0, y=0;
		int color=0;
		bool active = false;
		
		Piece() { }
		Piece(unsigned short data[16]) 
		{
			for(int i=0;i<16;i++) this->data[i]=data[i];
		}
	};
	
	void Piece_move_y(Piece* piece, int dy) { piece->y+=dy; }
	void Piece_move_x(Piece* piece, int dx) { piece->x+=dx; }	
	
	Piece piece_templates[] = {
		Piece((unsigned short[16]){0,1,0,0, 0,1,0,0, 0,1,0,0, 0,1,0,0}),
		Piece((unsigned short[16]){0,0,0,0, 0,1,1,0, 0,1,1,0, 0,0,0,0}),
		Piece((unsigned short[16]){0,0,0,0, 0,1,1,0, 0,0,1,1, 0,0,0,0}),
		Piece((unsigned short[16]){0,0,0,0, 0,0,1,1, 0,1,1,0, 0,0,0,0}),
		Piece((unsigned short[16]){0,1,1,0, 0,1,0,0, 0,1,0,0, 0,0,0,0}),
		Piece((unsigned short[16]){0,1,1,0, 0,0,1,0, 0,0,1,0, 0,0,0,0}),
	};
	
	int left_key_down();
	int right_key_down();
	int down_key_held();
	
	struct GameState
	{	
		BufferView board;		
		int board_width = 10;
		int board_height = 18;
		Piece current_piece{};
		
		unsigned short backup_data[16]{};
		
		GameState(unsigned short* bgmap, int stride, int left, int top, int width, int height)
			: board(BufferView(&bgmap[top*stride+left], stride))			
			, board_width{width}
			, board_height{height}
		{ }
		
		void push_piece()
		{
			for(int y=0;y<4;y++)
			{
				for(int x=0;x<4;x++)
				{
					backup_data[4*y+x] = 0;
					if(current_piece.data[4*y+x]==0) continue;
					int gy = current_piece.y + y;			
					int gx = current_piece.x + x;
					if(gy<0 || gx<0 || gy>=board_height || gx>=board_width) continue;
					backup_data[4*y+x] = board[gy][gx];
					board[gy][gx] = current_piece.data[4*y+x] * current_piece.color;
				}
			}
		}
		
		void pop_piece()
		{
			for(int y=0;y<4;y++)
			{
				for(int x=0;x<4;x++)
				{					
					if(current_piece.data[4*y+x]==0) continue;
					int gy = current_piece.y + y;			
					int gx = current_piece.x + x;
					if(gy<0 || gx<0 || gy>=board_height || gx>=board_width) continue;
					board[gy][gx] = backup_data[4*y+x];
				}
			}
			
		}
		
	};
	
	Piece* GameState_generate_random_piece(GameState* gs)
	{
		int ix = rand()%(sizeof(piece_templates)/sizeof(Piece));
		gs->current_piece = piece_templates[ix];		
		gs->current_piece.color = 2+rand()%6;
		gs->current_piece.x = gs->board_width/2-2;
		return &gs->current_piece;
	}
	
	int GameState_test_piece(GameState* gs, Piece* piece)
	{
		for(int y=0;y<4;y++)
		{			
			for(int x=0;x<4;x++)
			{
				if(piece->data[4*y+x]!=0)
				{
					int gy = piece->y+y;
					int gx = piece->x+x;
					if(gy<0 || gx<0 || gy>=gs->board_height || gx>=gs->board_width)
						return 0;
					if(gs->board[gy][gx]!=0)
						return 0;
				}
			}
		}
		return 1;
	}
	
	int GameState_piece_move_if_possible(GameState* gs, Piece* piece, int dx, int dy)
	{
		piece->x+=dx; piece->y+=dy;		
		if (!GameState_test_piece(gs, piece))
		{
			piece->x-=dx; piece->y-=dy;			
			return 0;
		}
		return 1;
	}
	
	void GameState_reset(GameState* gs)
	{
		for(int y=0;y<gs->board_height;y++)
		{
			for(int x=0;x<gs->board_width;x++)
			{
				gs->board[y][x]=0;
			}
		}
	}
	
	void GameState_place_piece(GameState* gs, Piece* piece)
	{
		for(int y=0;y<4;y++)
		{			
			for(int x=0;x<4;x++)
			{
				if(piece->data[4*y+x]!=0)
				{
					int gy = piece->y+y;
					int gx = piece->x+x;
					if(gy<0 || gx<0 || gy>=gs->board_height || gx>=gs->board_width)
						continue;
					gs->board[gy][gx] = piece->data[4*y+x]*piece->color;
				}
			}
		}
	}
	
}