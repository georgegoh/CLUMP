/*
 * Copyright (c) 2003 SuSE Linux AG Nuernberg, Germany.
 * Author: Thorsten Kukuk <kukuk@suse.de>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, and the entire permission notice in its entirety,
 *    including the disclaimer of warranties.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote
 *    products derived from this software without specific prior
 *    written permission.
 *
 * ALTERNATIVELY, this product may be distributed under the terms of
 * the GNU Public License, in which case the provisions of the GPL are
 * required INSTEAD OF the above restrictions.  (This clause is
 * necessary due to a potential bad interaction between the GPL and
 * the restrictions contained in a BSD-style copyright.)
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __GETUSER_H__
#define __GETUSER_H__

#include <pwd.h>
#include <shadow.h>
#include <security/pam_modules.h>

enum service_t {S_NONE, S_LOCAL, S_YP, S_LDAP};

struct user_t {
  char *pwdbuffer;
  size_t pwdbuflen;
  struct passwd pwd;
  char *spwbuffer;
  size_t spwbuflen;
  struct spwd spw;
  enum service_t service;
  int use_shadow;
  int is_expired;
  int is_tooearly;
  int is_expiring;
  int use_hp_aging;
  int hp_min;
  int hp_max;
  int hp_week;
  char *oldpassword;
  char *oldclearpwd;
  char *newpassword;
};
typedef struct user_t user_t;

user_t *__do_getpwnam (const char *user, char *nisdir);
void free_user_t (user_t *data);
int __get_passwd (pam_handle_t *pamh, const char *msgs, char **passwd);

#endif /* __GET_USER_H__ */
