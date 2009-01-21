/* Copyright (C) 2003 Thorsten Kukuk
   Author: Thorsten Kukuk <kukuk@suse.de>

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License version 2 as
   published by the Free Software Foundation.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  */

#ifndef _LOGINDEFS_H_

#define _LOGINDEFS_H_ 1

extern int getlogindefs_bool (const char *name, int dflt);
extern long getlogindefs_num (const char *name, long dflt);
extern unsigned long getlogindefs_unum (const char *name, unsigned long dflt);
extern const char *getlogindefs_str (const char *name, const char *dflt);

/* Free all data allocated by getlogindefs_* calls before.  */
extern void free_getlogindefs_data (void);

#endif /* _LOGINDEFS_H_ */
