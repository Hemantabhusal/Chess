/*
  Stockfish, a UCI chess playing engine derived from Glaurung 2.1
  Copyright (C) 2004-2008 Tord Romstad (Glaurung author)
  Copyright (C) 2008-2010 Marco Costalba, Joona Kiiski, Tord Romstad

  Stockfish is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  Stockfish is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


#if !defined(DEPTH_H_INCLUDED)
#define DEPTH_H_INCLUDED

#include "types.h"

////
//// Types
////

enum Depth {

  ONE_PLY = 2,

  DEPTH_ZERO         =  0 * ONE_PLY,
  DEPTH_QS_CHECKS    = -1 * ONE_PLY,
  DEPTH_QS_NO_CHECKS = -2 * ONE_PLY,

  DEPTH_NONE = -127 * ONE_PLY
};

ENABLE_OPERATORS_ON(Depth);

#endif // !defined(DEPTH_H_INCLUDED)
